from flask import Flask
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST, Gauge
import asyncio
from kasa import Device, Module
import os

HS300_IP = os.environ.get("PLUG_IP")

app = Flask(__name__)


async def get_metrics() -> dict:
    output_dict = {}
    try:
        dev = await Device.connect(host=HS300_IP)
        await dev.update()
        str = ""
        str += f"Host: {dev.host}\n"
        str += f"Alias: {dev.alias}\n"
        str += f"Model: {dev.model}\n"
        str += f"Device Type: {dev.device_type}\n"
        for plug in dev.children:
            str += f"Plug: {plug.alias}\n"
            energy = plug.modules[Module.Energy]
            str += f"Current Consumption: {energy.current_consumption}w\n"
            output_dict[plug.alias] = energy.current_consumption
        return output_dict
    except Exception as e:
        return f"HS300_IP: {HS300_IP} ------------ Got Nothing: error: {e}"


@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()

    # Run asyncio task inside Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(get_metrics())
    try:
        for key, value in data.items():
            g = Gauge(
                f"kasa_power_watts_{key}", f"Power consumption in watts for {key}", registry=registry)
            g.set(value)
        return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    except Exception as e:
        return data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9101)
