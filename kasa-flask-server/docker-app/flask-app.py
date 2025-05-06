from flask import Flask
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST, Gauge
import asyncio
from kasa import Device, Module, DeviceConnectionParameters, DeviceConfig, Credentials, DeviceFamily, DeviceEncryptionType
import os

# user config
HS300_IP = os.getenv("HS300_IP")
KP125M_IPS = os.getenv("KP125M_IPS").split(",")
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

app = Flask(__name__)


async def get_metrics_HS300(ip: str) -> dict:
    output_dict = {}
    try:
        dev = await Device.connect(host=ip)
        await dev.update()
        for plug in dev.children:
            energy = plug.modules[Module.Energy]
            output_dict[plug.alias] = energy.current_consumption
        return output_dict
    except Exception as e:
        return f"IP: {ip} ------------ Got Nothing: error: {e}"


async def get_metrics_KP125M(ip_list: list[str]) -> dict:
    output_dict = {}
    for ip in ip_list:
        try:
            device_config = DeviceConfig(
                host=ip,
                credentials=Credentials(
                    username=KASA_USERNAME, password=KASA_PASSWORD
                ),
                connection_type=KASA_KP125M_DEVICE_CONNECT_PARAM,
            )
            dev = await Device.connect(config=device_config)
            await dev.update()
            energy = dev.modules[Module.Energy]
            output_dict[dev.alias] = energy.current_consumption
        except Exception as e:
            return f"IP: {ip} ------------ Got Nothing: error: {e}"
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
        return hs300_data, 500, {'Content-Type': CONTENT_TYPE_LATEST}
    else:
        data = {**hs300_data, **kp125m_data}
        g = Gauge(name=NAME,
                    documentation=f"Power consumption in watts for each device",
                    labelnames=["device"],
                    unit="watts",
                    registry=registry)
        for key, value in data.items():
            g.labels(device=key).set(value)
        return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9101)
