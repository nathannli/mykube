import asyncio
from kasa import (
    Device,
    DeviceConfig,
)
from pprint import pp


async def main():
    ip = "195.168.1.226"
    dev = await Device.connect(config=DeviceConfig(host=ip, timeout=10))
    print(dev)
    await dev.update()
    pp(dev.children)


if __name__ == "__main__":
    asyncio.run(main())