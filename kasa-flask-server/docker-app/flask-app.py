from flask import Flask, Response
from kasa import SmartPlug
from prometheus_client import CollectorRegistry, Gauge, generate_latest
import asyncio
import os

HS300_IP = os.environ.get("PLUG_IP")

app = Flask(__name__)

async def get_metrics():
    plug = SmartPlug(HS300_IP)
    await plug.update()
    emeter = plug.emeter_realtime if plug.has_emeter else {}

    return {
        "power_watts": emeter.get("power_mw", 0) / 1000,
        "voltage_volts": emeter.get("voltage_mv", 0) / 1000,
        "current_amps": emeter.get("current_ma", 0) / 1000,
        "energy_kwh": emeter.get("total_wh", 0) / 1000,
    }

@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()
    power = Gauge("kasa_power_watts", "Power consumption in watts", registry=registry)
    voltage = Gauge("kasa_voltage_volts", "Voltage in volts", registry=registry)
    current = Gauge("kasa_current_amps", "Current in amps", registry=registry)
    energy = Gauge("kasa_energy_kwh", "Total energy used in kWh", registry=registry)

    # Run asyncio task inside Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(get_metrics())

    power.set(data["power_watts"])
    voltage.set(data["voltage_volts"])
    current.set(data["current_amps"])
    energy.set(data["energy_kwh"])

    return Response(generate_latest(registry), mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100)
