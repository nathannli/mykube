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


def require_list_env(name: str) -> list[str]:
    value = require_env(name)
    items = []
    for line in value.splitlines():
        line = line.strip()
        if line.startswith("-"):
            line = line[1:].strip()
        for part in line.split(","):
            part = part.strip()
            if part:
                items.append(part)
    return items


class Config:
    # Auth (kasa-secrets)
    # Kasa cloud account username used to authenticate with local devices.
    KASA_USERNAME = require_env("KASA_USERNAME")
    # Kasa cloud account password used to authenticate with local devices.
    KASA_PASSWORD = require_env("KASA_PASSWORD")

    # Device IPs (kasa-config)
    # IP address of the Kasa HS300 smart power strip.
    HS300_IP: str = require_env("HS300_IP")
    # Dash-delimited list of IP addresses for Kasa KP125M smart plugs.
    KP125M_IPS_RAW: str = require_env("KP125M_IPS")
    KP125M_IPS: list[str] = [x.strip() for x in KP125M_IPS_RAW.split("-") if x != ""]

    # Poweroff policy (kasa-config)
    # Plug aliases for desktops managed by the poweroff sequence.
    DESKTOPS: list[str] = require_list_env("DESKTOPS")
    # Plug aliases for radiators that are turned off after managed desktops are off.
    RADIATORS: list[str] = require_list_env("RADIATORS")
    # Desktop plug aliases skipped during poweroff and excluded from the radiator off-check.
    RADIATOR_POWEROFF_EXCLUDED_DEVICES: list[str] = require_list_env(
        "RADIATOR_POWEROFF_EXCLUDED_DEVICES"
    )
    # Wattage below which an on desktop plug is considered idle and safe to power off.
    LOW_POWER_THRESHOLD_WATTS: int = int(require_env("LOW_POWER_THRESHOLD_WATTS"))

    # Other device groups (kasa-config)
    # Outlet aliases expected on the HS300 smart power strip.
    HS300_DEVICE_NAME_LIST: list[str] = require_list_env("HS300_DEVICE_NAME_LIST")
    # Plug aliases for monitors (tracked in metrics, not turned off by desktop poweroff).
    MONITORS: list[str] = require_list_env("MONITORS")

    # Alerts and metrics
    # Webhook URL for sending plug and radiator poweroff alerts to Discord.
    DISCORD_ALERT_BOT_URL: str = require_env("DISCORD_ALERT_BOT_URL")
    NAME = "kasapower"

    # Protocol / connection parameters
    KASA_KP125M_DEVICE_CONNECT_PARAM = DeviceConnectionParameters(
        device_family=DeviceFamily.SmartKasaPlug,
        encryption_type=DeviceEncryptionType.Klap,
        login_version=2,
        https=False,
        http_port=80,
    )
    # The HS300 firmware update moved it off the legacy port 9999 protocol to
    # KLAP with login_version 2 (sha256 handshake hashes) on port 80.
    KASA_HS300_DEVICE_CONNECT_PARAM = DeviceConnectionParameters(
        device_family=DeviceFamily.IotSmartPlugSwitch,
        encryption_type=DeviceEncryptionType.Klap,
        login_version=2,
        https=False,
        http_port=80,
    )
    TPAP_KP125M_IPS = []
    KASA_TPAP_KP125M_DEVICE_CONNECT_PARAM = DeviceConnectionParameters(
        device_family=DeviceFamily.SmartKasaPlug,
        encryption_type=DeviceEncryptionType.Tpap,
        login_version=2,
        https=False,
        http_port=80,
    )

    @classmethod
    def get_kp125m_device_connect_param(cls, ip: str) -> DeviceConnectionParameters:
        if ip in cls.TPAP_KP125M_IPS:
            return cls.KASA_TPAP_KP125M_DEVICE_CONNECT_PARAM
        return cls.KASA_KP125M_DEVICE_CONNECT_PARAM

    def __repr__(self):
        return (
            f"Config(HS300_IP={self.HS300_IP}, KP125M_IPS={self.KP125M_IPS}, "
            f"RADIATOR_POWEROFF_EXCLUDED_DEVICES={self.RADIATOR_POWEROFF_EXCLUDED_DEVICES})"
        )
