import os

from kasa import DeviceConnectionParameters, DeviceEncryptionType, DeviceFamily


class Config:
    # user config
    HS300_IP: str = os.getenv("HS300_IP")
    KP125M_IPS_RAW: str = os.getenv("KP125M_IPS")
    KP125M_IPS: list[str] = [x.strip() for x in KP125M_IPS_RAW.split('-') if x != '']
    NAME = "kasapower"
    KASA_USERNAME = os.getenv("KASA_USERNAME")
    KASA_PASSWORD = os.getenv("KASA_PASSWORD")

    KASA_KP125M_DEVICE_CONNECT_PARAM = DeviceConnectionParameters(
        device_family=DeviceFamily.SmartKasaPlug,
        encryption_type=DeviceEncryptionType.Klap,
        login_version=2,
        https=False,
        http_port=80,
    )

    HS300_DEVICE_NAME_LIST = ["13k", "14kf", "9950x", "radiator", "alienware", "285k"]
    DO_NOT_TURN_OFF_LIST = ["radiator", "alienware", "odyssey-g9-57", "macmini", "Sound"]

    LOW_POWER_THRESHOLD_WATTS = 5

    # discord msg alerts
    DISCORD_ALERT_BOT_URL = "http://discord-general-channel-alert-bot-node-port.discord-bots.svc.cluster.local:5000/alert"
