import asyncio
import os
from typing import Any
import logging
import sys

from flask import Flask, jsonify
from kasa import (
    Device,
    Module,
    DeviceConnectionParameters,
    DeviceConfig,
    Credentials,
    DeviceFamily,
    DeviceEncryptionType,
)
from prometheus_client import (
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    Gauge,
)

# user config
HS300_IP: str = os.getenv("HS300_IP")
KP125M_IPS: str = os.getenv("KP125M_IPS").split(",")
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
DO_NOT_TURN_OFF_LIST = ["Radiator", "alienware", "odysey-g9-57"]

LOW_POWER_THRESHOLD_WATTS = 5

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


async def get_metrics_HS300(ip: str) -> dict[Any, Any] | str:
    output_dict = {}
    dev = await Device.connect(host=ip)
    try:
        await dev.update()
        for plug in dev.children:
            plug_name: str = plug.alias
            energy = plug.modules[Module.Energy]
            energy_consumption: int = energy.current_consumption
            # if the power is below operating threshold, turn off the plug
            if energy_consumption < LOW_POWER_THRESHOLD_WATTS:
                await power_off_plug_HS300(plug_name, dev)
            output_dict[plug_name] = energy_consumption
        return output_dict
    except Exception as e:
        return f"IP: {ip} ------------ Got Nothing: error: {e}"
    finally:
        await dev.disconnect()


async def power_off_radiator_HS300(ip: str) -> bool:
    plug_name: str = "Radiator"
    dev = await Device.connect(host=ip)
    try:
        await dev.update()
        for plug in dev.children:
            if plug.alias is not None and plug.alias.lower() == plug_name.lower():
                await plug.turn_off()
                log.info(f"Turned off plug {plug_name}")
                return True
        logger.warning(f"Plug {plug_name} not found")
        return False
    except Exception as e:
        logger.error(f"IP: {ip} ------------ Got Nothing: error: {e}")
        return False


async def power_off_plug_HS300(plug_name: str, dev: Device) -> bool | str:
    try:
        await dev.update()
        for plug in dev.children:
            if (
                plug.alias is not None
                and plug.alias.lower() == plug_name.lower()
                and plug.alias not in DO_NOT_TURN_OFF_LIST
            ):
                await plug.turn_off()
                logger.info(f"Turned off plug {plug_name}")
                return True
        logger.warning(f"Plug {plug_name} not found")
        return False
    except Exception as e:
        return f"Fail to turn off {plug_name}: {dev.host} | {e}"


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
            # if the power is below operating threshold, turn off the plug
            if energy_consumption < LOW_POWER_THRESHOLD_WATTS:
                await power_off_plug_KP125M(device_alias, dev)
            output_dict[device_alias] = energy_consumption
        except Exception as e:
            return f"IP: {ip} ------------ Got Nothing: error: {e}"
        finally:
            await dev.disconnect()
    return output_dict


async def power_off_plug_KP125M(plug_name: str, dev: Device) -> bool | str:
    if dev.alias is not None and dev.alias not in DO_NOT_TURN_OFF_LIST:
        try:
            await dev.update()
            await dev.turn_off()
            logger.info(f"Turned off plug {plug_name}")
            return True
        except Exception as e:
            logger.error(f"Fail to turn off {plug_name}: {dev.host} | {e}")
            return False
    else:
        return False


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


@app.route("/poweroffradiator", methods=["POST"])
def trigger_power_off():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(power_off_radiator_HS300(HS300_IP))
        return jsonify({"status": "success", "message": "radiator power off"}), 200
    except Exception as e:
        logger.exception(f"power off error: {e}")
        return jsonify(
            {
                "status": "radiator power off failure",
                "message": "radiator power off failure",
            }
        ), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9101)
