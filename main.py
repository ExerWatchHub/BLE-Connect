import asyncio
from ble_connect.BLEConnect import BLEConnect

async def main():
    app = BLEConnect()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
