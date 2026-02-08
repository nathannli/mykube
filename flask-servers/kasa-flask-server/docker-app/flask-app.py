import asyncio
import re
from contextlib import asynccontextmanager
from typing import Any

import requests
from config import Config
from flask import Flask, jsonify
from kasa import (
    Credentials,
    Device,
    DeviceConfig,
    Module,
)
from kasa.exceptions import _ConnectionError
from my_logger import Logger
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Gauge,
    generate_latest,
)
from time_of_use_electricity_pricing import TimeOfUseElectricityPricing

CONFIG = Config()
LOGGER = Logger().get_logger()
LOGGER.info(f"Loaded config: {CONFIG}")
TOU_PRICING = TimeOfUseElectricityPricing()

app = Flask(__name__)


def obscure_credentials(message: str) -> str:
    # Regex to find URLs with credentials: scheme://username:password@host/...
    return re.sub(r"(ftp://)([^:/\s]+):([^@/\s]+)@", r"\1nnn:nnn@", message)


async def send_discord_message(message: str) -> None:
    """Send a message to Discord webhook asynchronously with error handling."""
    try:
        payload_dict = {"message": obscure_credentials(message)}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: requests.post(CONFIG.DISCORD_ALERT_BOT_URL, json=payload_dict, timeout=5)
        )
    except Exception as e:
        LOGGER.error(f"Failed to send Discord message: {e}")


def should_manage_plug(plug: Any) -> bool:
    """Check if plug should be managed (turned off/monitored)."""
    return plug.alias is not None and plug.alias in CONFIG.DESKTOPS


def log_device_error(ip: str, error: Exception, context: str = "Got Nothing"):
    """Log device-related errors with consistent formatting."""
    LOGGER.error(f"IP: {ip} ------------ {context}: error: {error}")


async def connect_to_device(device_config: DeviceConfig, ip: str, max_retries: int = 3) -> Device:
    """Connect to a device with retry logic."""
    for attempt in range(max_retries):
        try:
            return await Device.connect(config=device_config)
        except (TimeoutError, OSError, _ConnectionError) as e:
            if attempt < max_retries - 1:
                LOGGER.warning(f"IP: {ip} - Connection error on attempt {attempt + 1}/{max_retries}, retrying in 10 seconds: {e}")
                await asyncio.sleep(10)
            else:
                LOGGER.error(f"IP: {ip} - Failed after {max_retries} attempts: {e}")
                raise


async def connect_to_kp125m_device(ip: str, timeout: int = 10, max_retries: int = 3) -> Device:
    """Connect to a KP125M device with credentials, retrying on timeout."""
    device_config = DeviceConfig(
        host=ip,
        credentials=Credentials(
            username=CONFIG.KASA_USERNAME, password=CONFIG.KASA_PASSWORD
        ),
        connection_type=CONFIG.KASA_KP125M_DEVICE_CONNECT_PARAM,
        timeout=timeout,
    )
    return await connect_to_device(device_config, ip, max_retries)


async def connect_to_hs300_device(ip: str, timeout: int = 10, max_retries: int = 3) -> Device:
    """Connect to an HS300 device, retrying on timeout."""
    device_config = DeviceConfig(host=ip, timeout=timeout)
    return await connect_to_device(device_config, ip, max_retries)


@asynccontextmanager
async def managed_device_connection(connect_func, *args, **kwargs):
    """Context manager for device connections with automatic disconnect."""
    dev = await connect_func(*args, **kwargs)
    try:
        await dev.update()
        yield dev
    finally:
        await dev.disconnect()


async def get_metrics_HS300(ip: str) -> dict[Any, Any]:
    output_dict = {}
    try:
        async with managed_device_connection(connect_to_hs300_device, ip) as dev:
            for plug in dev.children:
                plug_name = plug.alias
                if plug_name is not None:
                    energy = plug.modules[Module.Energy]
                    energy_consumption = energy.current_consumption
                    if energy_consumption is not None:
                        output_dict[plug_name] = int(energy_consumption)
        return output_dict
    except Exception as e:
        log_device_error(ip, e)
        raise e


async def turn_off_desktop_plugs_if_no_power_HS300(ip: str) -> bool:
    try:
        async with managed_device_connection(connect_to_hs300_device, ip) as dev:
            for plug in dev.children:
                if should_manage_plug(plug):
                    if plug.is_on:
                        plug_energy = plug.modules[Module.Energy]
                        if (
                            plug_energy.current_consumption
                            < CONFIG.LOW_POWER_THRESHOLD_WATTS
                        ):
                            await plug.turn_off()
                            await send_discord_message(f"Plug {plug.alias} turned off")
                        else:
                            LOGGER.warning(f"Plug {plug.alias} is still on")
                            return False
        return True
    except Exception as e:
        log_device_error(ip, e)
        return False


async def check_all_desktop_plugs_are_off_HS300() -> bool:
    try:
        async with managed_device_connection(connect_to_hs300_device, CONFIG.HS300_IP) as dev:
            for plug in dev.children:
                if should_manage_plug(plug):
                    if plug.is_on:
                        LOGGER.warning(f"Plug {plug.alias} is still on")
                        return False
        return True
    except Exception as e:
        log_device_error(CONFIG.HS300_IP, e)
        return False


async def power_off_radiator_HS300() -> bool:
    """
    powers off radiator plug if all other plugs are off
    and powers off Sound plug if the above is true
    """
    plug_name: str = "radiator"
    all_plugs_are_off = await check_all_desktop_plugs_are_off_HS300() and await check_all_desktop_plugs_are_off_KP125M(CONFIG.KP125M_IPS)
    if all_plugs_are_off:
        try:
            async with managed_device_connection(connect_to_hs300_device, CONFIG.HS300_IP) as dev:
                for plug in dev.children:
                    if plug.alias is not None and plug.alias.lower() == plug_name.lower():
                        if plug.is_on:
                            await plug.turn_off()
                            await send_discord_message(f"Plug {plug.alias} turned off")
                        return True
                LOGGER.warning(f"Plug {plug_name} not found")
                return False
        except Exception as e:
            log_device_error(CONFIG.HS300_IP, e)
            return False
    else:
        return False


async def check_all_desktop_plugs_are_off_KP125M(ip_list: list[str]) -> bool:
    for ip in ip_list:
        try:
            async with managed_device_connection(connect_to_kp125m_device, ip) as dev:
                if should_manage_plug(dev) and dev.is_on:
                    LOGGER.error(f"Plug {dev.alias} is still on")
                    return False
        except Exception as e:
            log_device_error(ip, e)
            return False
    return True


async def turn_off_desktop_plugs_if_no_power_KP125M(ip_list: list[str]) -> bool:
    for ip in ip_list:
        try:
            async with managed_device_connection(connect_to_kp125m_device, ip) as dev:
                if should_manage_plug(dev) and dev.is_on:
                    device_energy = dev.modules[Module.Energy]
                    if device_energy.current_consumption < CONFIG.LOW_POWER_THRESHOLD_WATTS:
                        await dev.turn_off()
                        await send_discord_message(f"Plug {dev.alias} turned off")
                    else:
                        LOGGER.warning(f"Plug {dev.alias} is still on")
                        return False
        except Exception as e:
            log_device_error(ip, e)
            return False
    return True


async def power_off_sound_KP125M(ip: str) -> bool:
    """
    return true if off
    return false if error or still on
    """
    try:
        async with managed_device_connection(connect_to_kp125m_device, ip) as dev:
            if dev.alias and dev.alias.lower() == "sound" and dev.is_on:
                await dev.turn_off()
                await send_discord_message(f"Plug {dev.alias} turned off")
        return True
    except Exception as e:
        log_device_error(ip, e)
        return False


async def get_metrics_KP125M(ip_list: list[str]) -> dict[Any, Any]:
    output_dict = {}
    for ip in ip_list:
        try:
            async with managed_device_connection(connect_to_kp125m_device, ip) as dev:
                device_alias = dev.alias
                if device_alias is not None:
                    energy = dev.modules[Module.Energy]
                    energy_consumption = energy.current_consumption
                    if energy_consumption is not None:
                        output_dict[device_alias] = int(energy_consumption)
        except _ConnectionError as ce:
            log_device_error(ip, ce, "Connection Error")
            continue
        except TimeoutError as te:
            log_device_error(ip, te, "Timeout Error")
            continue
        except Exception as e:
            log_device_error(ip, e)
            raise e
    return output_dict


@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()

    # Run asyncio task inside Flask
    hs300_data = {}
    kp125m_data = {}

    try:
        hs300_data = asyncio.run(get_metrics_HS300(CONFIG.HS300_IP))
    except Exception as e:
        LOGGER.error(f"Error in metrics route from get_metrics_HS300: {e}")
    try:
        kp125m_data = asyncio.run(get_metrics_KP125M(CONFIG.KP125M_IPS))
    except Exception as e:
        LOGGER.error(f"Error in metrics route from get_metrics_KP125M: {e}")

    data = {**hs300_data, **kp125m_data}

    # gauge for devices
    g = Gauge(
        name=CONFIG.NAME,
        documentation="Power consumption in watts for each device",
        labelnames=["device"],
        unit="watts",
        registry=registry,
    )
    for key, value in data.items():
        g.labels(device=key).set(value)

    # Gauge for electricity price
    price_gauge = Gauge(
        name="electricity_price",
        documentation="Current electricity price in CAD per kWh",
        registry=registry,
    )
    price_gauge.set(TOU_PRICING.get_current_price())
    # LOGGER.info(TOU_PRICING)

    return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}
    


async def trigger_power_off_desktops_async():
    """Execute power off sequence for all devices."""
    await turn_off_desktop_plugs_if_no_power_HS300(CONFIG.HS300_IP)
    await turn_off_desktop_plugs_if_no_power_KP125M(CONFIG.KP125M_IPS)
    result = await power_off_radiator_HS300()
    if result and CONFIG.ENABLE_SOUND_DEVICE_CHECK:
        if CONFIG.KP125M_SOUND_IP is None:
            LOGGER.warning("ENABLE_SOUND_DEVICE_CHECK is true but KP125M_SOUND_IP is not set")
            return
        await power_off_sound_KP125M(CONFIG.KP125M_SOUND_IP)
    if result and not CONFIG.ENABLE_SOUND_DEVICE_CHECK:
        LOGGER.info("Skipping sound device check because ENABLE_SOUND_DEVICE_CHECK is disabled")


@app.route("/poweroff", methods=["POST"])
def trigger_power_off():
    try:
        asyncio.run(trigger_power_off_desktops_async())
        return jsonify({"status": "success", "message": "poweroff success"}), 200
    except Exception as e:
        LOGGER.exception(f"power off error: {e}")
        return jsonify(
            {
                "status": "failure",
                "message": "power off failure",
            }
        ), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9101)
