import asyncio
import re
from typing import Any
import atexit

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

CONFIG = Config()
LOGGER = Logger().get_logger()

app = Flask(__name__)

# create shared event loop
# LOOP = asyncio.new_event_loop()
# asyncio.set_event_loop(LOOP)


# @atexit.register
# def shutdown_event_loop():
#     LOGGER.info("Shutting down event loop")
#     LOOP.stop()
#     LOOP.close()
#     LOGGER.info("Event loop closed")


def obscure_credentials(message):
    # Regex to find URLs with credentials: scheme://username:password@host/...
    return re.sub(r"(ftp://)([^:/\s]+):([^@/\s]+)@", r"\1nnn:nnn@", message)


def send_discord_message(message):
    payload_dict = {"message": obscure_credentials(message)}
    requests.post(CONFIG.DISCORD_ALERT_BOT_URL, json=payload_dict)


async def get_metrics_HS300(ip: str) -> dict[Any, Any]:
    output_dict = {}
    dev = await Device.connect(host=ip)
    try:
        await dev.update()
        for plug in dev.children:
            plug_name: str = plug.alias
            energy = plug.modules[Module.Energy]
            energy_consumption: int = energy.current_consumption
            output_dict[plug_name] = energy_consumption
        return output_dict
    except Exception as e:
        LOGGER.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
        raise e
    finally:
        await dev.disconnect()


async def turn_off_plugs_if_no_power_HS300(ip: str) -> bool:
    dev = await Device.connect(host=ip)
    try:
        await dev.update()
        for plug in dev.children:
            if plug.alias is not None and plug.alias not in CONFIG.DO_NOT_TURN_OFF_LIST:
                if plug.is_on:
                    plug_energy = plug.modules[Module.Energy]
                    if (
                        plug_energy.current_consumption
                        < CONFIG.LOW_POWER_THRESHOLD_WATTS
                    ):
                        await plug.turn_off()
                        send_discord_message(f"Plug {plug.alias} turned off")
                    else:
                        LOGGER.warning(f"Plug {plug.alias} is still on")
                        return False
    except Exception as e:
        LOGGER.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
        return False
    finally:
        await dev.disconnect()
    return True


async def check_all_plugs_are_off_HS300(ip: str) -> bool:
    dev = await Device.connect(host=ip)
    try:
        await dev.update()
        for plug in dev.children:
            if plug.alias is not None and plug.alias not in CONFIG.DO_NOT_TURN_OFF_LIST:
                if plug.is_on:
                    LOGGER.warning(f"Plug {plug.alias} is still on")
                    return False
    except Exception as e:
        LOGGER.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
        return False
    finally:
        await dev.disconnect()
    return True


async def power_off_radiator_HS300() -> bool:
    plug_name: str = "Radiator"
    dev = await Device.connect(host=CONFIG.HS300_IP)
    all_plugs_are_off = await check_all_plugs_are_off_HS300(
        CONFIG.HS300_IP
    ) and await check_all_plugs_are_off_KP125M(CONFIG.KP125M_IPS)
    if all_plugs_are_off:
        try:
            await dev.update()
            for plug in dev.children:
                if plug.alias is not None and plug.alias.lower() == plug_name.lower():
                    if plug.is_on:
                        await plug.turn_off()
                        send_discord_message(f"Plug {plug.alias} turned off")
                    return True
            LOGGER.warning(f"Plug {plug_name} not found")
            return False
        except Exception as e:
            LOGGER.error(f"IP: {CONFIG.HS300_IP} ------------ Got Nothing: error: {e}")
            return False
    else:
        return False


async def check_all_plugs_are_off_KP125M(ip_list: list[str]) -> bool:
    for ip in ip_list:
        device_config = DeviceConfig(
            host=ip,
            credentials=Credentials(
                username=CONFIG.KASA_USERNAME, password=CONFIG.KASA_PASSWORD
            ),
            connection_type=CONFIG.KASA_KP125M_DEVICE_CONNECT_PARAM,
            timeout=10,
        )
        dev = await Device.connect(config=device_config)
        try:
            await dev.update()
            if dev.alias not in CONFIG.DO_NOT_TURN_OFF_LIST and dev.is_on:
                LOGGER.error(f"Plug {dev.alias} is still on")
                return False
        except Exception as e:
            LOGGER.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
            return False
        finally:
            await dev.disconnect()
    return True


async def turn_off_plugs_if_no_power_KP125M(ip_list: list[str]) -> bool:
    for ip in ip_list:
        device_config = DeviceConfig(
            host=ip,
            credentials=Credentials(
                username=CONFIG.KASA_USERNAME, password=CONFIG.KASA_PASSWORD
            ),
            connection_type=CONFIG.KASA_KP125M_DEVICE_CONNECT_PARAM,
        )
        dev = await Device.connect(config=device_config)
        try:
            await dev.update()
            if dev.alias not in CONFIG.DO_NOT_TURN_OFF_LIST and dev.is_on:
                device_energy = dev.modules[Module.Energy]
                if device_energy.current_consumption < CONFIG.LOW_POWER_THRESHOLD_WATTS:
                    await dev.turn_off()
                    send_discord_message(f"Plug {dev.alias} turned off")
                else:
                    LOGGER.error(f"Plug {dev.alias} is still on")
                    return False
        except Exception as e:
            LOGGER.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
            return False
        finally:
            await dev.disconnect()
    return True


async def get_metrics_KP125M(ip_list: list[str]) -> dict[Any, Any]:
    output_dict = {}
    for ip in ip_list:
        device_config = DeviceConfig(
            host=ip,
            credentials=Credentials(
                username=CONFIG.KASA_USERNAME, password=CONFIG.KASA_PASSWORD
            ),
            connection_type=CONFIG.KASA_KP125M_DEVICE_CONNECT_PARAM,
        )
        try:
            dev = await Device.connect(config=device_config)
        except _ConnectionError as ce:
            LOGGER.error(f"IP: {ip} ------------ Connection Error: {ce}")
            continue
        except TimeoutError as te:
            LOGGER.error(f"IP: {ip} ------------ Timeout Error: {te}")
            continue
        try:
            await dev.update()
            device_alias: str = dev.alias
            energy = dev.modules[Module.Energy]
            energy_consumption: int = energy.current_consumption
            output_dict[device_alias] = energy_consumption
        except Exception as e:
            LOGGER.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
            raise e
        finally:
            await dev.disconnect()
    return output_dict


@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()

    # Run asyncio task inside Flask
    hs300_data = {}
    kp125m_data = {}
    try:
        # hs300_data = LOOP.run_until_complete(get_metrics_HS300(CONFIG.HS300_IP))
        hs300_data = asyncio.run(get_metrics_HS300(CONFIG.HS300_IP))
    except Exception as e:
        LOGGER.error(f"Error in metrics route from get_metrics_HS300: {e}")
    try:
        # kp125m_data = LOOP.run_until_complete(get_metrics_KP125M(CONFIG.KP125M_IPS))
        kp125m_data = asyncio.run(get_metrics_KP125M(CONFIG.KP125M_IPS))
        data = {**hs300_data, **kp125m_data}
        g = Gauge(
            name=CONFIG.NAME,
            documentation="Power consumption in watts for each device",
            labelnames=["device"],
            unit="watts",
            registry=registry,
        )
        for key, value in data.items():
            g.labels(device=key).set(value)
        return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}
    except Exception as e:
        LOGGER.error(f"Error in metrics: {e}")
        return (
            "there was an error in the flask app",
            500,
            {"Content-Type": CONTENT_TYPE_LATEST},
        )


@app.route("/poweroff", methods=["POST"])
def trigger_power_off():
    try:
        # LOOP.run_until_complete(turn_off_plugs_if_no_power_HS300(CONFIG.HS300_IP))
        asyncio.run(turn_off_plugs_if_no_power_HS300(CONFIG.HS300_IP))
        # LOOP.run_until_complete(turn_off_plugs_if_no_power_KP125M(CONFIG.KP125M_IPS))
        asyncio.run(turn_off_plugs_if_no_power_KP125M(CONFIG.KP125M_IPS))
        # LOOP.run_until_complete(power_off_radiator_HS300())
        asyncio.run(power_off_radiator_HS300())
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
