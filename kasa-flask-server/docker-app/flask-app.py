from flask import Flask, Response
from prometheus_client import Summary
import asyncio
import os
import asyncio
from kasa import Device, Module

HS300_IP = os.environ.get("PLUG_IP")

app = Flask(__name__)

async def get_metrics():
    output_dict = {}

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
    return str

@app.route("/metrics")
def metrics():
    # s = Summary("kasa_power_watts", "Power consumption in watts")

    # Run asyncio task inside Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(get_metrics())
    return data
    # for key, value in data.items():


    # return Response(generate_latest(registry), mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100)
