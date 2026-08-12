import importlib.util
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch


APP_PATH = Path(__file__).parent.parent / "docker-app" / "flask-app.py"
APP_DIR = APP_PATH.parent
sys.path.insert(0, str(APP_DIR))
os.environ.setdefault("HS300_IP", "10.20.0.40")
os.environ.setdefault("KP125M_IPS", "10.20.0.1")
os.environ.setdefault("KASA_USERNAME", "test")
os.environ.setdefault("KASA_PASSWORD", "test")

spec = importlib.util.spec_from_file_location("kasa_flask_app", APP_PATH)
flask_app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = flask_app
spec.loader.exec_module(flask_app)


def test_kp125m_failure_does_not_discard_other_metrics():
    good_device = type(
        "Device",
        (),
        {
            "alias": "LG45",
            "modules": {
                flask_app.Module.Energy: type(
                    "Energy", (), {"current_consumption": 28.0}
                )()
            },
        },
    )()

    good_device.disconnect = AsyncMock()

    with patch.object(
        flask_app,
        "connect_to_kp125m_device",
        AsyncMock(
            side_effect=[
                good_device,
                RuntimeError("TPAP discover response missing tpap object"),
            ]
        ),
    ):

        assert asyncio.run(
            flask_app.get_metrics_KP125M(["10.20.0.1", "10.20.0.2"])
        ) == {
            "LG45": 28
        }
