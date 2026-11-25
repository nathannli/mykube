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


def _make_device(alias, is_on=True):
    dev = type("Device", (), {"alias": alias, "is_on": is_on})()
    dev.turn_off = AsyncMock()
    dev.disconnect = AsyncMock()
    return dev


def test_radiator_turns_off_when_all_desktops_off():
    """Gate passes -> radiator turn_off() is awaited."""
    radiator = _make_device("radiator")

    with patch.object(
        flask_app,
        "connect_to_kp125m_device",
        AsyncMock(return_value=radiator),
    ), patch.object(
        flask_app,
        "check_all_desktop_plugs_are_off_HS300",
        AsyncMock(return_value=True),
    ), patch.object(
        flask_app,
        "check_all_desktop_plugs_are_off_KP125M",
        AsyncMock(return_value=True),
    ), patch.object(
        flask_app,
        "send_discord_message",
        AsyncMock(),
    ):
        asyncio.run(flask_app.trigger_power_off_desktops_async())

    radiator.turn_off.assert_awaited()


def test_radiator_untouched_when_desktop_still_on():
    """Gate fails -> radiator is never turned off (core new behavior)."""
    radiator = _make_device("radiator")

    with patch.object(
        flask_app,
        "connect_to_kp125m_device",
        AsyncMock(return_value=radiator),
    ), patch.object(
        flask_app,
        "check_all_desktop_plugs_are_off_HS300",
        AsyncMock(return_value=False),
    ), patch.object(
        flask_app,
        "check_all_desktop_plugs_are_off_KP125M",
        AsyncMock(return_value=True),
    ):
        asyncio.run(flask_app.trigger_power_off_desktops_async())

    radiator.turn_off.assert_not_awaited()


def test_radiator_alias_not_in_desktops():
    """Guards accidental list edits: radiator must never match DESKTOPS."""
    assert "radiator" not in flask_app.CONFIG.DESKTOPS
    assert "radiator" in flask_app.CONFIG.RADIATORS

    radiator = _make_device("radiator", is_on=True)
    assert not flask_app.should_manage_plug(radiator)
    assert flask_app.should_manage_radiator(radiator)


def _make_energy_device(alias, is_on=True, watts=100.0):
    dev = type(
        "Device",
        (),
        {
            "alias": alias,
            "is_on": is_on,
            "modules": {
                flask_app.Module.Energy: type(
                    "Energy", (), {"current_consumption": watts}
                )()
            },
        },
    )()

    async def _turn_off():
        dev.is_on = False

    dev.turn_off = AsyncMock(side_effect=_turn_off)
    dev.disconnect = AsyncMock()
    return dev


def _make_hs300(children):
    strip = type("HS300", (), {"children": children})()
    strip.disconnect = AsyncMock()
    return strip


def test_excluded_hs300_device_on_still_turns_off_radiator():
    """Excluded HS300 desktop stays on -> non-excluded idle desktop turns off -> radiator turns off."""
    excluded_pc = _make_energy_device("13kf", is_on=True, watts=150.0)
    idle_pc = _make_energy_device("14kf", is_on=True, watts=2.0)
    hs300 = _make_hs300([excluded_pc, idle_pc])
    radiator = _make_energy_device("radiator", is_on=True, watts=500.0)

    with patch.object(
        flask_app,
        "connect_to_hs300_device",
        AsyncMock(return_value=hs300),
    ), patch.object(
        flask_app,
        "connect_to_kp125m_device",
        AsyncMock(return_value=radiator),
    ), patch.object(
        flask_app,
        "send_discord_message",
        AsyncMock(),
    ):
        asyncio.run(
            flask_app.trigger_power_off_desktops_async(excluded_devices=["13kf"])
        )

    excluded_pc.turn_off.assert_not_awaited()
    idle_pc.turn_off.assert_awaited_once()
    radiator.turn_off.assert_awaited_once()


def test_excluded_kp125m_device_on_still_turns_off_radiator():
    """Excluded KP125M desktop stays on -> radiator still turns off."""
    hs300 = _make_hs300([_make_energy_device("13kf", is_on=False, watts=0.0)])
    excluded_kp = _make_energy_device("9600k", is_on=True, watts=120.0)
    radiator = _make_energy_device("radiator", is_on=True, watts=500.0)
    kp_by_ip = {"10.20.0.1": excluded_kp, "10.20.0.2": radiator}

    async def fake_kp_connect(ip, *args, **kwargs):
        return kp_by_ip[ip]

    with patch.object(
        flask_app.CONFIG,
        "KP125M_IPS",
        ["10.20.0.1", "10.20.0.2"],
    ), patch.object(
        flask_app,
        "connect_to_hs300_device",
        AsyncMock(return_value=hs300),
    ), patch.object(
        flask_app,
        "connect_to_kp125m_device",
        AsyncMock(side_effect=fake_kp_connect),
    ), patch.object(
        flask_app,
        "send_discord_message",
        AsyncMock(),
    ):
        asyncio.run(
            flask_app.trigger_power_off_desktops_async(excluded_devices=["9600k"])
        )

    excluded_kp.turn_off.assert_not_awaited()
    radiator.turn_off.assert_awaited_once()


def test_non_excluded_device_on_blocks_radiator_even_with_exclusions():
    """Another non-excluded desktop still on -> radiator stays on."""
    excluded_pc = _make_energy_device("13kf", is_on=True, watts=150.0)
    other_pc = _make_energy_device("14kf", is_on=True, watts=80.0)
    hs300 = _make_hs300([excluded_pc, other_pc])
    radiator = _make_energy_device("radiator", is_on=True, watts=500.0)

    with patch.object(
        flask_app,
        "connect_to_hs300_device",
        AsyncMock(return_value=hs300),
    ), patch.object(
        flask_app,
        "connect_to_kp125m_device",
        AsyncMock(return_value=radiator),
    ), patch.object(
        flask_app,
        "send_discord_message",
        AsyncMock(),
    ):
        asyncio.run(
            flask_app.trigger_power_off_desktops_async(excluded_devices=["13kf"])
        )

    radiator.turn_off.assert_not_awaited()


def test_config_default_exclusions_used_when_no_override():
    """CONFIG.RADIATOR_POWEROFF_EXCLUDED_DEVICES applies when excluded_devices is None."""
    excluded_pc = _make_energy_device("14ks", is_on=True, watts=90.0)
    hs300 = _make_hs300([excluded_pc])
    radiator = _make_energy_device("radiator", is_on=True, watts=500.0)

    with patch.object(
        flask_app.CONFIG,
        "RADIATOR_POWEROFF_EXCLUDED_DEVICES",
        ["14ks"],
    ), patch.object(
        flask_app,
        "connect_to_hs300_device",
        AsyncMock(return_value=hs300),
    ), patch.object(
        flask_app,
        "connect_to_kp125m_device",
        AsyncMock(return_value=radiator),
    ), patch.object(
        flask_app,
        "send_discord_message",
        AsyncMock(),
    ):
        asyncio.run(flask_app.trigger_power_off_desktops_async())

    radiator.turn_off.assert_awaited_once()


def test_poweroff_route_accepts_exclude_list():
    """POST /poweroff forwards JSON exclude list to trigger_power_off_desktops_async."""
    client = flask_app.app.test_client()
    mock_trigger = AsyncMock()

    with patch.object(flask_app, "trigger_power_off_desktops_async", mock_trigger):
        resp = client.post("/poweroff", json={"exclude": ["13kf", "9600k"]})

    assert resp.status_code == 200
    mock_trigger.assert_awaited_once_with(excluded_devices=["13kf", "9600k"])


def test_poweroff_route_rejects_invalid_exclude_type():
    """POST /poweroff returns 400 if exclude is not a list of strings."""
    client = flask_app.app.test_client()
    resp = client.post("/poweroff", json={"exclude": "13kf"})
    assert resp.status_code == 400
