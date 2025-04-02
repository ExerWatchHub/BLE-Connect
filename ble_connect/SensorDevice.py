from bleak import BleakClient, BLEDevice, AdvertisementData, BleakGATTCharacteristic
import asyncio
import dearpygui.dearpygui as dpg
import platform

from .config import EXER_BLE_SERVICE_UUID, EXER_CHARACTERISTIC_UUID_TX, EXER_CHARACTERISTIC_UUID_RX, WATCH_CHARACTERISTIC_UUID_RX, WATCH_CHARACTERISTIC_UUID_TX, TEST_SERVICE_UUIDS, FILTERED_DEVICES, AUTO_CONNECT, BG_LOOP


class SensorDevice(BLEDevice):
    def __init__(self, ble_device: BLEDevice = None, address: str = "LOCAL_ADDRESS", name: str = "MOCK_DEVICE", ad_data: AdvertisementData = None):
        rssi = 0 if ad_data is None else ad_data.rssi
        if ble_device is not None:
            super(SensorDevice, self).__init__(ble_device.address, ble_device.name, ble_device.details, rssi)
        else:
            super(SensorDevice, self).__init__(address, name, None, rssi)
        self.ad_data: AdvertisementData = ad_data
        self.client: BleakClient = BleakClient(self.address)
        self.is_paused = False
        self.is_updated = False
        self.is_exerwatch = False
        self.is_accepted_device = False
        self.is_selected = False
        self.is_connected = False
        self.is_updating = False 
        self.widget = None

    async def update(self, data: AdvertisementData):
        if self.is_updating:
            # print(f"Device {self.name} is already updating!")
            return
        self.is_updating = True
        if data is None or self.name is None:
            self.is_updating = False
            return
        if self.is_updated or self.is_connected:
            self.is_updating = False
            return
        print(f"Updating device {self.name} {self.address}")

        self.is_exerwatch = any(map(lambda x: x.upper() in [EXER_BLE_SERVICE_UUID]+TEST_SERVICE_UUIDS, data.service_uuids))
        if not self.is_exerwatch:
            self.is_updated = True
            self.is_updating = False
            # print(f"Device {self.name} is NOT an ExerWatch device!")
            return

        if FILTERED_DEVICES is None or len(FILTERED_DEVICES) <= 0:
            self.is_accepted_device = True
        else:
            self.is_accepted_device = (str(self.name).upper() in FILTERED_DEVICES or str(self.address).upper() in FILTERED_DEVICES)
            
        if not self.is_accepted_device:
            self.is_updated = True
            self.is_updating = False
            print(f"Device {self.name} is an ExerWatch sensor but it is NOT in the list of accepted devices!: {FILTERED_DEVICES}")
            return

        if self.is_connected:
            self.is_updated = True
            self.is_updating = False
            print(f"Device {self.name} is already connected!")
            return
        if not AUTO_CONNECT:
            self.is_updated = True
            self.is_updating = False
            print(f"Device {self.name} ready to connect! (AUTO_CONNECT=False)")
            return

        try:
            self.widget.on_accepted_device()
        except Exception as e:
            print(f"Exception updating device widget: {e}")
        print("\t - Attempting connection to device...")
        await self.connect()
        try:
            await self.client.connect()
        except Exception as e:
            print(f"Exception connecting to device: {self}: {e}")
        self.is_updated = True
        self.is_updating = False

    def notification_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        self.widget.on_notification(characteristic, data)

    def toggle_connect(self):
        if self.is_connected:
            asyncio.run_coroutine_threadsafe(self.disconnect(), BG_LOOP)
        else:
            asyncio.run_coroutine_threadsafe(self.connect(), BG_LOOP)

    async def disconnect(self):
        await self.client.stop_notify(EXER_CHARACTERISTIC_UUID_TX)
        await self.client.disconnect()
        self.is_connected = False
        if self.widget is not None:
            self.widget.on_disconnect()

    async def connect(self):
        if self.is_connected:
            return print(f"Device {self.name} is already connected!")
        try:
            print(f"Connecting to {self.name} {self.address}... ")
            await self.client.connect()
            self.is_connected = True
            print(f"CONNECTED to {self.name} {self.address}!")
        except Exception as e:
            print(f"Exception connecting to device: {self}: {e}")
            return

        if self.widget is not None:
            self.widget.on_connect()   

        await self.start_notifications()
        await self.send_name_to_device()


    async def start_notifications(self):
        try:
            # Start receiving notifications on the GATT characteristic advertising the sensor's IMU data
            await self.client.start_notify(EXER_CHARACTERISTIC_UUID_TX, self.notification_handler)
        except Exception as e:
            print(f"Exception starting notificaitons for gatt '{EXER_CHARACTERISTIC_UUID_TX}': {e}")
            
    async def send_name_to_device(self):
        device_name = platform.node() # Get the name of this device (e.g. the macbook's name)
        characteristics = None
        descriptors = None
        try:
            await self.client.write_gatt_char(WATCH_CHARACTERISTIC_UUID_RX, bytearray(f"n{device_name}", "utf-8"))
            characteristics = self.client.services.characteristics
        except Exception as e:
            print(f"Exception writing to gatt '{WATCH_CHARACTERISTIC_UUID_RX}': {e}")
            
        try:
            await self.client.write_gatt_char(EXER_CHARACTERISTIC_UUID_RX, bytearray(f"n{device_name}", "utf-8"))
            descriptors = self.client.services.descriptors
        except Exception as e:
            print(f"Exception writing to gatt '{EXER_CHARACTERISTIC_UUID_RX}': {e}")

        if self.widget is not None:
            self.widget.on_services_discovered(characteristics, descriptors)


class LocalFileMockDevice(SensorDevice):
    def __init__(self, *args, **kwargs):
        super(LocalFileMockDevice, self).__init__(*args, **kwargs)
        self.is_connected = True
