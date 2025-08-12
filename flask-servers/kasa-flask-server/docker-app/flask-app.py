import asyncio
import logging
import os
import re
import sys
from typing import Any

import requests
from flask import Flask, jsonify
from kasa import (
    Credentials,
    Device,
    DeviceConfig,
    DeviceConnectionParameters,
    DeviceEncryptionType,
    DeviceFamily,
    Module,
)
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Gauge,
    generate_latest,
)

# user config
HS300_IP: str = os.getenv("HS300_IP")
KP125M_IPS: list[str] = os.getenv("KP125M_IPS").split(",")
NAME = "kasapower"
KASA_USERNAME = os.getenv("KASA_USERNAME")
KASA_PASSWORD = os.getenv("KASA_PASSWORD")

KASA_KP125M_DEVICE_CONNECT_PARAM = DeviceConnectionParameters(
    device_family=DeviceFamily.SmartKasaPlug,
    encryption_type=DeviceEncryptionType.Klap,
    login_version=2,
    https=False,
    http_port=80,
)

HS300_DEVICE_NAME_LIST = ["13k", "14kf", "14ks", "9950x", "Radiator"]
DO_NOT_TURN_OFF_LIST = ["Radiator", "alienware", "odyssey-g9-57", "macmini"]

LOW_POWER_THRESHOLD_WATTS = 5

# discord msg alerts
DISCORD_ALERT_BOT_URL = "http://discord-general-channel-alert-bot-node-port.discord-bots.svc.cluster.local:5000/alert"

# init logging
# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # or DEBUG for more details

# Create handler that logs to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# Optional: set a log message format
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s"
)
handler.setFormatter(formatter)

# Add the handler to the root logger
logger.addHandler(handler)

# Disable Flask's default logging to prevent duplicate logs (optional)
logging.getLogger("werkzeug").disabled = True

app = Flask(__name__)


def obscure_credentials(message):
    # Regex to find URLs with credentials: scheme://username:password@host/...
    return re.sub(r"(ftp://)([^:/\s]+):([^@/\s]+)@", r"\1nnn:nnn@", message)


def send_discord_message(message):
    payload_dict = {"message": obscure_credentials(message)}
    requests.post(DISCORD_ALERT_BOT_URL, json=payload_dict)


async def get_metrics_HS300(ip: str) -> dict[Any, Any] | str:
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
        return f"IP: {ip} ------------ Got Nothing: error: {e}"
    finally:
        await dev.disconnect()


async def turn_off_plugs_if_no_power_HS300(ip: str) -> bool:
    dev = await Device.connect(host=ip)
    try:
        await dev.update()
        for plug in dev.children:
            if plug.alias is not None and plug.alias not in DO_NOT_TURN_OFF_LIST:
                if plug.is_on:
                    plug_energy = plug.modules[Module.Energy]
                    if plug_energy.current_consumption < LOW_POWER_THRESHOLD_WATTS:
                        await plug.turn_off()
                        send_discord_message(f"Plug {plug.alias} turned off")
                    else:
                        logger.error(f"Plug {plug.alias} is still on")
                        return False
    except Exception as e:
        logger.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
        return False
    finally:
        await dev.disconnect()
    return True


async def check_all_plugs_are_off_HS300(ip: str) -> bool:
    dev = await Device.connect(host=ip)
    try:
        await dev.update()
        for plug in dev.children:
            if plug.alias is not None and plug.alias not in DO_NOT_TURN_OFF_LIST:
                if plug.is_on:
                    logger.error(f"Plug {plug.alias} is still on")
                    return False
    except Exception as e:
        logger.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
        return False
    finally:
        await dev.disconnect()
    return True


async def power_off_radiator_HS300() -> bool:
    plug_name: str = "Radiator"
    dev = await Device.connect(host=HS300_IP)
    all_plugs_are_off = await check_all_plugs_are_off_HS300(
        HS300_IP
    ) and check_all_plugs_are_off_KP125M(KP125M_IPS)
    if all_plugs_are_off:
        try:
            await dev.update()
            for plug in dev.children:
                if plug.alias is not None and plug.alias.lower() == plug_name.lower():
                    await plug.turn_off()
                    send_discord_message(f"Plug {plug.alias} turned off")
                    return True
            logger.warning(f"Plug {plug_name} not found")
            return False
        except Exception as e:
            logger.error(f"IP: {HS300_IP} ------------ Got Nothing: error: {e}")
            return False
    else:
        return False


async def check_all_plugs_are_off_KP125M(ip_list: list[str]) -> bool:
    for ip in ip_list:
        device_config = DeviceConfig(
            host=ip,
            credentials=Credentials(username=KASA_USERNAME, password=KASA_PASSWORD),
            connection_type=KASA_KP125M_DEVICE_CONNECT_PARAM,
        )
        dev = await Device.connect(config=device_config)
        try:
            await dev.update()
            if dev.alias not in DO_NOT_TURN_OFF_LIST and dev.is_on:
                logger.error(f"Plug {dev.alias} is still on")
                return False
        except Exception as e:
            logger.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
            return False
        finally:
            await dev.disconnect()
    return True


async def turn_off_plugs_if_no_power_KP125M(ip_list: list[str]) -> bool:
    for ip in ip_list:
        device_config = DeviceConfig(
            host=ip,
            credentials=Credentials(username=KASA_USERNAME, password=KASA_PASSWORD),
            connection_type=KASA_KP125M_DEVICE_CONNECT_PARAM,
        )
        dev = await Device.connect(config=device_config)
        try:
            await dev.update()
            if dev.alias not in DO_NOT_TURN_OFF_LIST and dev.is_on:
                device_energy = dev.modules[Module.Energy]
                if device_energy.current_consumption < LOW_POWER_THRESHOLD_WATTS:
                    await dev.turn_off()
                    send_discord_message(f"Plug {dev.alias} turned off")
                else:
                    logger.error(f"Plug {dev.alias} is still on")
                    return False
        except Exception as e:
            logger.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
            return False
        finally:
            await dev.disconnect()
    return True


async def get_metrics_KP125M(ip_list: list[str]) -> str | dict[Any, Any]:
    output_dict = {}
    for ip in ip_list:
        device_config = DeviceConfig(
            host=ip,
            credentials=Credentials(username=KASA_USERNAME, password=KASA_PASSWORD),
            connection_type=KASA_KP125M_DEVICE_CONNECT_PARAM,
        )
        dev = await Device.connect(config=device_config)
        try:
            await dev.update()
            device_alias: str = dev.alias
            energy = dev.modules[Module.Energy]
            energy_consumption: int = energy.current_consumption
            output_dict[device_alias] = energy_consumption
        except Exception as e:
            return f"IP: {ip} ------------ Got Nothing: error: {e}"
        finally:
            await dev.disconnect()
    return output_dict


@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()

    # Run asyncio task inside Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    hs300_data = loop.run_until_complete(get_metrics_HS300(HS300_IP))
    kp125m_data = loop.run_until_complete(get_metrics_KP125M(KP125M_IPS))
    if type(hs300_data) == str or type(kp125m_data) == str:
        logger.error(f"hs300_data: {hs300_data}")
        logger.error(f"kp125m_data: {kp125m_data}")
        return (
            "there was an error in the flask app",
            500,
            {"Content-Type": CONTENT_TYPE_LATEST},
        )
    else:
        data = {**hs300_data, **kp125m_data}
        g = Gauge(
            name=NAME,
            documentation="Power consumption in watts for each device",
            labelnames=["device"],
            unit="watts",
            registry=registry,
        )
        for key, value in data.items():
            g.labels(device=key).set(value)
        return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/poweroff", methods=["POST"])
def trigger_power_off():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(turn_off_plugs_if_no_power_HS300(HS300_IP))
        loop.run_until_complete(turn_off_plugs_if_no_power_KP125M(KP125M_IPS))
        loop.run_until_complete(power_off_radiator_HS300())
        return jsonify({"status": "success", "message": "poweroff success"}), 200
    except Exception as e:
        logger.exception(f"power off error: {e}")
        return jsonify(
            {
                "status": "failure",
                "message": "power off failure",
            }
        ), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9101)
