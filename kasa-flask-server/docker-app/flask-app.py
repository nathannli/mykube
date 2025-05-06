from flask import Flask
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST, Gauge
import asyncio
from kasa import Device, Module
import os

# user config
HS300_IP = "195.168.1.69"
KP303_IP = "195.168.1.65"
KP125M_IP = "195.168.1.66"
KASA_DEVICES = [HS300_IP, KP303_IP, KP125M_IP]
NAME = "kasapower"

app = Flask(__name__)


async def get_metrics(ip_list: list[str]) -> dict:
    output_dict = {}
    for ip in ip_list:
        try:
            dev = await Device.connect(host=ip)
            await dev.update()
            for plug in dev.children:
                energy = plug.modules[Module.Energy]
                output_dict[plug.alias] = energy.current_consumption
        except Exception as e:
            return f"IP: {ip} ------------ Got Nothing: error: {e}"
    return output_dict


@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()

    # Run asyncio task inside Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(get_metrics(KASA_DEVICES))
    if type(data) == str:
        return data, 500, {'Content-Type': CONTENT_TYPE_LATEST}
    else:
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
