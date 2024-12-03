from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak import BleakClient, BleakScanner
import logging
import argparse
import asyncio
from bleak import BleakScanner

logger = logging.getLogger(__name__)


async def scan():
    devices = await BleakScanner.discover()
    return devices

def main():
    asyncio.run(scan())


if __name__ == "__main__":
    main()