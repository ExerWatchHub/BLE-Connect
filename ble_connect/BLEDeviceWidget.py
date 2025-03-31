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
from .IMUDataWidget import IMUDataWidget
from .config import EXER_BLE_SERVICE_UUID, EXER_CHARACTERISTIC_UUID_TX, EXER_CHARACTERISTIC_UUID_RX, WATCH_CHARACTERISTIC_UUID_RX, WATCH_CHARACTERISTIC_UUID_TX, TEST_SERVICE_UUIDS, FILTERED_DEVICES, AUTO_CONNECT


class BLEDeviceWidget:
    def __init__(self, app, device: BLEDevice, data: AdvertisementData = None, foldout_container: str = None, panel_container: str = None, exer_sensors_container: str = None, separate_window: bool = True):
        self.app = app
        self.themes = self.app.themes
        self.theme = self.themes.generic_device
        self.foldout_tag = f"{device.address}_foldout"
        self.selectable_tag = f"{device.address}_selectable"
        self.panel_tag = f"{device.address}_panel"
        self.button_tag = f"{device.address}_button"
        self.device: BLEDevice = device
        self.data: AdvertisementData = data
        self.client: BleakClient = BleakClient(device.address)
        self.foldout_container = foldout_container
        self.panel_container = panel_container
        self.exer_sensors_container = exer_sensors_container
        self.on_click = None
        self.handler_registry = dpg.add_item_handler_registry()
        self.click_handler = -1
        self.imu_data = IMUDataWidget(app, self.device, connect_callback=self.connect_callback)
        self.device_processed = False
        self.is_exerwatch = False
        self.is_accepted_device = False
        self.is_selected = False
        self.is_connected = False
        self.device_processed = False
        self.separate_window = separate_window
        if self.foldout_container is not None:
            self.foldout_info(self.foldout_container)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_theme()

    def on_device_click(self, sender, app_data):
        print(f"Object clicked: {sender}")
        self.device_info(self.panel_container)
        try:
            self.on_click(sender, app_data, self)
        except Exception as e:
            print(f"Exception on click: {e}")

    def device_info(self, container: str = None):
        container = self.panel_container if container is None else container
        try:
            dpg.delete_item(container, children_only=True)
        except Exception as e:
            print(f"Exception deleting items: {e}")
        with dpg.group(parent=container, tag=self.panel_tag) as grp:
            dpg.add_text(tag=f"{self.panel_tag}_address", default_value=f"{self.device.address}")
            dpg.add_text(tag=f"{self.panel_tag}_name", default_value=f"{self.device.name}")
            try:
                dpg.add_text(tag=f"{self.panel_tag}_service_uuids", default_value=f"{list(map(lambda x: str(x.uuid), self.client.services.services.values()))}")
            except Exception as e:
                pass
            dpg.add_text(tag=f"{self.panel_tag}_service_data", default_value=f"{self.data.service_data}")
            dpg.add_text(tag=f"{self.panel_tag}_manufacturer_data", default_value=f"{self.data.manufacturer_data}")
            dpg.add_text(tag=f"{self.panel_tag}_platform_data", default_value=f"{self.data.platform_data}")
            dpg.add_text(tag=f"{self.panel_tag}_rssi", default_value=f"{self.data.rssi}")
            dpg.add_text(tag=f"{self.panel_tag}_services", default_value=f"{self.data.rssi}")

    def foldout_info(self, container: str = None):
        container = self.foldout_container if container is None else container
        with dpg.group(parent=container, filter_key=f"{self.device.name}", horizontal=True, tag=self.foldout_tag) as grp:
            dpg.add_button(tag=self.button_tag, label=f"Connect", callback=self.connect_callback, user_data=self.device, enabled=True, show=False)
            dpg.add_collapsing_header(label=f"{self.device.name} ({self.device.address})", tag=self.selectable_tag, closable=False, leaf=True)

        dpg.bind_item_handler_registry(self.selectable_tag, self.handler_registry)
        self.click_handler = dpg.add_item_clicked_handler(parent=self.handler_registry, callback=self.on_device_click)
        dpg.bind_item_theme(self.foldout_tag, self.themes.generic_device)

    def connect_callback(self, sender="Internal", app_data=None, device=None):
        if device is None:
            device = self.device
        if self.is_connected:
            asyncio.run_coroutine_threadsafe(self.disconnect(device), self.app.bg_loop)
        else:
            asyncio.run_coroutine_threadsafe(self.connect(device), self.app.bg_loop)

    def notification_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        dpg.set_item_label(self.selectable_tag, f"{self.device.name} ({self.device.address}) => {data.decode('utf-8')}")
        self.imu_data.update(data)
        # self.imu_data2.update(data)
        # print(f"{characteristic.description}: {data}")

    async def disconnect(self, device):
        await self.client.stop_notify(EXER_CHARACTERISTIC_UUID_TX)
        await self.client.disconnect()
        self.is_connected = False
        dpg.configure_item(self.button_tag, label="Connect")
        dpg.set_item_label(self.selectable_tag, f"{self.device.name} ({self.device.address})")

    async def connect(self, device):
        try:
            print(f"Connecting to {device.name} {device.address}")
            await self.client.connect()
            self.is_connected = True
            dpg.configure_item(self.button_tag, label="Disconnect")
        except Exception as e:
            print(f"Exception connecting to device: {device}: {e}")
            return

        # Start receiving notifications on the GATT characteristic advertising the sensor's IMU data
        try:
            await self.client.start_notify(EXER_CHARACTERISTIC_UUID_TX, self.notification_handler)
        except Exception as e:
            print(f"Exception starting notificaitons for gatt '{EXER_CHARACTERISTIC_UUID_TX}': {e}")

        # Send the device name to the sensor
        try:
            device_name = platform.node()
            await self.client.write_gatt_char(WATCH_CHARACTERISTIC_UUID_RX, bytearray(f"n{device_name}", "utf-8"))
            await self.client.write_gatt_char(EXER_CHARACTERISTIC_UUID_RX, bytearray(f"n{device_name}", "utf-8"))
            characteristics = self.client.services.characteristics
            str_data = list(map(lambda x: f"{x.uuid}: {x.description}", characteristics.values()))
            descriptors = self.client.services.descriptors
            str_data += list(map(lambda x: f"{x.uuid}: {x.description}", descriptors.values()))
            dpg.set_value(f"{self.panel_tag}_services", '\n - '.join(str_data))
        except Exception as e:
            print(f"Exception writing to gatt '{EXER_CHARACTERISTIC_UUID_RX}': {e}")

    def update_theme(self):
        # dpg.configure_item(self.selectable_tag, selected=self.is_selected)
        self.theme = self.themes.generic_device
        if self.is_selected:
            self.theme = self.themes.selected_device
        elif self.is_exerwatch:
            self.theme = self.themes.exer_device
        # print(f"Updating theme for {self.device.name}: {self.theme} ")
        dpg.bind_item_theme(self.foldout_tag, self.theme)
        dpg.configure_item(self.button_tag, show=self.is_exerwatch)

    def add_widget(self, container: str = None):
        container = self.exer_sensors_container if container is None else container
        self.imu_data.add_widget(self.exer_sensors_container, separate_window=self.separate_window)
        # self.imu_data2.add_widget(self.exer_sensors_container)

    def update(self, data: AdvertisementData):
        if data is None or self.device.name is None:
            return
        if self.device_processed or self.is_connected:
            return
        
        self.is_exerwatch = any(map(lambda x: x.upper() in [EXER_BLE_SERVICE_UUID]+TEST_SERVICE_UUIDS, data.service_uuids))
        self.is_accepted_device = (str(self.device.name).upper() in FILTERED_DEVICES or str(self.device.address).upper() in FILTERED_DEVICES)
        if self.is_exerwatch:
            if self.is_accepted_device:
                if not self.is_connected and AUTO_CONNECT:
                    asyncio.run_coroutine_threadsafe(self.connect(self.device), self.app.bg_loop)
                self.update_theme()
                for i in range(len(self.app.devices.keys())):
                    dpg.move_item_up(self.foldout_tag)  # Move ExerWatch sensors all the way to the top
                self.add_widget()
            else:
                print(f"New device {self.device.name} is NOT in the list of accepted devices!: {FILTERED_DEVICES}")
        self.device_processed = True
