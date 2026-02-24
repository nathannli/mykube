import os

from kasa import DeviceConnectionParameters, DeviceEncryptionType, DeviceFamily


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"{name} environment variable is not set")
    return value


def get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # user config
    HS300_IP: str = require_env("HS300_IP")
    KP125M_SOUND_IP: str | None = os.getenv("KP125M_SOUND_IP")
    ENABLE_SOUND_DEVICE_CHECK: bool = KP125M_SOUND_IP is not None
    KP125M_IPS_RAW: str = require_env("KP125M_IPS")
    KP125M_IPS: list[str] = [x.strip() for x in KP125M_IPS_RAW.split('-') if x != '']
    NAME = "kasapower"
    KASA_USERNAME = require_env("KASA_USERNAME")
    KASA_PASSWORD = require_env("KASA_PASSWORD")

    KASA_KP125M_DEVICE_CONNECT_PARAM = DeviceConnectionParameters(
        device_family=DeviceFamily.SmartKasaPlug,
        encryption_type=DeviceEncryptionType.Klap,
        login_version=2,
        https=False,
        http_port=80,
    )

    HS300_DEVICE_NAME_LIST = ["13k", "14kf", "9950x", "7950x", "14ks", "285k"]
    MONITORS = ["odyssey-g9-57", "alienware", "LGDualUp"]
    DESKTOPS = ["13k", "14kf", "9950x", "285k", "7950x", "14ks"]
    RADIATOR_PLUG_TYPE = "KP125M"

    LOW_POWER_THRESHOLD_WATTS = 5

    # discord msg alerts
    DISCORD_ALERT_BOT_URL = "http://discord-general-channel-alert-bot-node-port.discord-bots.svc.cluster.local:5000/alert"

    def __repr__(self):
        return (
            f"Config(HS300_IP={self.HS300_IP}, KP125M_IPS={self.KP125M_IPS}, "
            f"ENABLE_SOUND_DEVICE_CHECK={self.ENABLE_SOUND_DEVICE_CHECK}, "
            f"KP125M_SOUND_IP={self.KP125M_SOUND_IP})"
        )
