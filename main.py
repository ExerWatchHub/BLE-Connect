from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak import BleakClient, BleakScanner, BLEDevice, AdvertisementData
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import dearpygui_ext.themes as dpg_themes
import logging
import argparse
from threading import Thread
import asyncio
import typing
import platform

EXER_BLE_SERVICE_UUID = "EC4D35AE-96DC-4385-81B2-64A17E67B13D".upper()
SERVICE_UUID: str = "6e400001-b5a3-f393-e0a9-e50e24dcca9e".upper() # UART service UUID
CHARACTERISTIC_UUID_RX: str = "6e400002-b5a3-f393-e0a9-e50e24dcca9e".upper() # Writable
CHARACTERISTIC_UUID_TX: str = "6e400003-b5a3-f393-e0a9-e50e24dcca9e".upper() # Notifiable
theme_1 = "theme_1"
theme_2 = "theme_2"


class BLEConnect:
    def __init__(self):
        dpg.create_context()
        self.connected_device = None
        self.devices: dict[str, BLEDeviceUI] = {}
        self.devices_list_id = dpg.generate_uuid()
        self.bg_loop = None
        self.scan_loading = "ble_scan_loading"
        self.filter_tag = "devices_filter"
        self.menubar = False
        self.stop_event = asyncio.Event()
        self.theme_1 = None
        
    def setup_bg_loop(self):
        self.bg_loop = asyncio.new_event_loop()
        def bleak_thread(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        t = Thread(target=bleak_thread, args=(self.bg_loop,))
        t.start()
        asyncio.run_coroutine_threadsafe(self.ble_scan(), self.bg_loop)
    
    async def ble_scan(self):
        dpg.configure_item(self.scan_loading, show=True)
        async with BleakScanner(lambda device, data: self.on_device_detected(device, data)) as scanner:
            # Important! Wait for an event to trigger stop, otherwise scannerwill stop immediately.
            await self.stop_event.wait()
        dpg.configure_item(self.scan_loading, show=False)
        
    def on_device_detected(self, device: BLEDevice, data: AdvertisementData):
        # print(f"Device detected: {device}")
        if device.address not in self.devices:
            device_ui = BLEDeviceUI(self, device, data, self.filter_tag)
            self.devices[device.address] = device_ui            
        self.devices[device.address].update(data)
        
    async def run(self):
        dpg.create_viewport()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self.make_themes()
        self.make_window("main_window")
        self.setup_bg_loop()
        # self.run_scan(None)
        
        dpg.start_dearpygui()
        dpg.destroy_context()
                
        self.bg_loop.call_soon_threadsafe(self.bg_loop.stop)        
        
    def make_themes(self):
        global theme_1, theme_2
        with dpg.theme(tag=theme_1) as container_theme:
            theme_1 = container_theme
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)

        with dpg.theme() as item_theme:
            theme_2 = item_theme
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Header, (101, 66, 52))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)
                
                
    def make_window(self, tag):
        # demo.show_demo()
        # dpg.configure_item("__demo_id", collapsed=True)
        # dpg.show_style_editor()
        with dpg.window(label="Example Window", tag=tag, autosize=True, menubar=self.menubar):
            if self.menubar:
                with dpg.menu_bar():
                    dpg.add_menu(label="Menu Options")
            self.devices_window()
        dpg.set_primary_window(tag, True)
        
    def devices_window(self):
        with dpg.group(horizontal=True):
            # dpg.add_button(label="BLE Scan", callback=self.run_scan)
            dpg.add_loading_indicator(circle_count=5, tag=self.scan_loading, show=True, radius=2, color=(255, 255, 255, 255))
        dpg.add_input_text(label="Name filter (inc, -exc)", user_data=self.filter_tag, callback=lambda sender, app_data, user_data: dpg.set_value(user_data, dpg.get_value(sender)))
        with dpg.child_window(tag=self.devices_list_id, autosize_x=True, auto_resize_y=True):
            dpg.add_filter_set(tag=self.filter_tag)\
                


class BLEDeviceUI:
    def __init__(self, app: BLEConnect, device: BLEDevice, data: AdvertisementData = None, parent: str = None):
        self.app = app
        self.tag = f"{device.address}"
        self.foldout_tag = f"{self.tag}_foldout"
        self.device: BLEDevice = device
        self.data: AdvertisementData = data
        self.client: BleakClient = BleakClient(device.address)
        self.is_exerwatch = False
        self.parent = parent
        if self.parent is not None:
            self.add_item(self.parent)

    def add_item(self, container: str):
        global theme_1, theme_2
        dpg.add_group(parent=container, filter_key=f"{self.device.name}", horizontal=True, tag=self.tag)
        dpg.add_button(parent=self.tag, tag=f"{self.tag}_button", label=f"Connect", callback=self.connect_button_callback, user_data=self.device, enabled=True)

        dpg.add_collapsing_header(parent=self.tag, label=f"{self.device.name} ({self.device.address})", tag=self.foldout_tag)
        dpg.add_input_int(parent=self.foldout_tag, label=" ", step=0)
        dpg.add_text(parent=self.foldout_tag, tag=f"{self.tag}_address", default_value=f"{self.device.address}")
        dpg.add_text(parent=self.foldout_tag, tag=f"{self.tag}_name", default_value=f"{self.device.name}")
        dpg.add_text(parent=self.foldout_tag, tag=f"{self.tag}_service_uuids", default_value=f"{self.data.service_uuids}")
        dpg.add_text(parent=self.foldout_tag, tag=f"{self.tag}_service_data", default_value=f"{self.data.service_data}")
        dpg.add_text(parent=self.foldout_tag, tag=f"{self.tag}_manufacturer_data", default_value=f"{self.data.manufacturer_data}")
        dpg.add_text(parent=self.foldout_tag, tag=f"{self.tag}_platform_data", default_value=f"{self.data.platform_data}")
        dpg.add_text(parent=self.foldout_tag, tag=f"{self.tag}_rssi", default_value=f"{self.data.rssi}")
        dpg.add_text(parent=self.foldout_tag, tag=f"{self.tag}_services", default_value=f"{self.data.rssi}")

        dpg.bind_item_theme(self.tag, theme_1)
        
    def connect_button_callback(self, sender, app_data, device):
        print(f"Sender: {sender}")
        print(f"App Data: {app_data}")
        asyncio.run_coroutine_threadsafe(self.connect(device), self.app.bg_loop)
        
    def notification_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        dpg.set_item_label(self.foldout_tag, f"{self.device.name} ({self.device.address}) => {data.decode("utf-8")}")
        # print(f"{characteristic.description}: {data}")
        
    async def disconnect(self):
        await self.client.stop_notify(CHARACTERISTIC_UUID_TX)
        await self.client.disconnect()
        dpg.set_item_label(self.foldout_tag, f"{self.device.name} ({self.device.address})")
        dpg.configure_item(f"{self.tag}_button", enabled=True)

    async def connect(self, device):
        try:
            print(f"Connecting to {device.address}")
            await self.client.connect()
        except Exception as e:
            print(f"Exception connecting to device: {device}: {e}")
            return
        dpg.configure_item(f"{self.tag}_button", enabled=False)
        # Start receiving notifications on the GATT characteristic advertising the sensor's IMU data
        try:
            await self.client.start_notify(CHARACTERISTIC_UUID_TX, self.notification_handler)
        except Exception as e:
            print(f"Exception starting notificaitons for gatt '{CHARACTERISTIC_UUID_TX}': {e}")
            
        # Send the device name to the sensor
        try:
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, bytearray(platform.node(), "utf-8"))
            characteristics = self.client.services.characteristics
            str_data = list(map(lambda x: f"{x.uuid}: {x.description}", characteristics.values()))
            descriptors = self.client.services.descriptors
            str_data += list(map(lambda x: f"{x.uuid}: {x.description}", descriptors.values()))
            dpg.set_value(f"{self.tag}_services", '\n - '.join(str_data))
        except Exception as e:
            print(f"Exception writing to gatt '{CHARACTERISTIC_UUID_RX}': {e}")


    def update(self, data: AdvertisementData):
        global theme_1, theme_2
        self.data = data
        if self.data is not None:
            if not self.is_exerwatch:
                self.is_exerwatch = any(map(lambda x: x.upper() == EXER_BLE_SERVICE_UUID, data.service_uuids))
                if self.is_exerwatch:
                    dpg.bind_item_theme(self.tag, theme_2)
                    # dpg.move_item(self.tag, parent=self.parent)
                    for i in range(len(self.app.devices.keys())):
                        dpg.move_item_up(self.tag) # Move ExerWatch sensors all the way to the top
        

async def main():
    app = BLEConnect()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
