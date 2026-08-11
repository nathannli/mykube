import asyncio
import importlib.util
import os
import sys
from pathlib import Path

import pytest
from kasa import DeviceEncryptionType

DOCKER_APP_DIR = Path(__file__).parent.parent / "docker-app"
sys.path.insert(0, str(DOCKER_APP_DIR))

os.environ.setdefault("HS300_IP", "10.20.0.40")
os.environ.setdefault("KP125M_IPS", "10.20.0.115")
os.environ.setdefault("KASA_USERNAME", "test-user")
os.environ.setdefault("KASA_PASSWORD", "test-password")

from config import Config

FLASK_APP_SPEC = importlib.util.spec_from_file_location(
    "kasa_flask_app", DOCKER_APP_DIR / "flask-app.py"
)
FLASK_APP = importlib.util.module_from_spec(FLASK_APP_SPEC)
FLASK_APP_SPEC.loader.exec_module(FLASK_APP)


@pytest.mark.parametrize(
    ("ip", "encryption_type"),
    [
        ("10.20.0.115", DeviceEncryptionType.Tpap),
        ("10.20.0.116", DeviceEncryptionType.Klap),
    ],
)
def test_kp125m_connection_param_uses_tpap_override(ip, encryption_type):
    connection_param = Config.get_kp125m_device_connect_param(ip)

    assert connection_param.encryption_type is encryption_type


def test_connect_to_kp125m_device_uses_selected_connection_param(monkeypatch):
    captured = {}

    async def fake_connect_to_device(device_config, ip, max_retries):
        captured["device_config"] = device_config
        captured["ip"] = ip
        captured["max_retries"] = max_retries
        return object()

    monkeypatch.setattr(FLASK_APP, "connect_to_device", fake_connect_to_device)

    asyncio.run(FLASK_APP.connect_to_kp125m_device("10.20.0.115", max_retries=1))

    assert captured["ip"] == "10.20.0.115"
    assert captured["max_retries"] == 1
    assert (
        captured["device_config"].connection_type.encryption_type
        is DeviceEncryptionType.Tpap
    )
