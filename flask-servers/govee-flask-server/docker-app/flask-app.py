from flask import Flask
from prometheus_client import (
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    Gauge,
)
import asyncio
import os
import requests

# user config
NAME = "govee"
GOVEE_API_KEY = os.getenv("GOVEE_API_KEY")
GOVEE_DEVICE_ID = os.getenv("GOVEE_DEVICE_ID")
GOVEE_DEVICE_SKU = os.getenv("GOVEE_DEVICE_SKU")
GOVEE_BASE_URL = "https://openapi.api.govee.com"
GOVEE_PROPERTIES_URL_SUFFIX = "/router/api/v1/device/state"

app = Flask(__name__)


async def get_temp_humidity(request_id: str) -> dict | str:
    output_dict = {}
    try:
        url = f"{GOVEE_BASE_URL}{GOVEE_PROPERTIES_URL_SUFFIX}"
        headers = {"Govee-API-Key": GOVEE_API_KEY, "Content-Type": "application/json"}
        body = {
            "requestId": request_id,
            "payload": {"sku": GOVEE_DEVICE_SKU, "device": GOVEE_DEVICE_ID},
        }
        response = requests.post(url, headers=headers, json=body)
        data = response.json()["payload"]["capabilities"]
        for element in data:
            if element["instance"] == "sensorTemperature":
                output_dict["temperatureF"] = float(element["state"]["value"])
            if element["instance"] == "sensorHumidity":
                output_dict["humidity"] = float(element["state"]["value"])
        return output_dict
    except Exception as e:
        return f"govee response error: {response.status_code} ------------ Got Nothing: error: {e}"


@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()

    # Run asyncio task inside Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    govee_data = loop.run_until_complete(get_temp_humidity(GOVEE_DEVICE_ID))
    if type(govee_data) == str:
        print(f"govee_data: {govee_data}")
        return (
            "there was an error in the flask app",
            500,
            {"Content-Type": CONTENT_TYPE_LATEST},
        )
    else:
        data = govee_data
        temp_gauge = Gauge(
            f"{NAME}_temperature",
            documentation=f"Temperature in F for the govee device",
            unit="F",
            registry=registry,
        )
        temp_gauge.set(data["temperatureF"])

        humidity_gauge = Gauge(
            f"{NAME}_humidity",
            documentation=f"Humidity in % for the govee device",
            unit="percentage",
            registry=registry,
        )
        humidity_gauge.set(data["humidity"])
        return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9101)
