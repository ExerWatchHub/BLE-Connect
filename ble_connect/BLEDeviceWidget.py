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
from .config import EXER_BLE_SERVICE_UUID, CHARACTERISTIC_UUID_TX, CHARACTERISTIC_UUID_RX, TEST_SERVICE_UUIDS

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
        self.imu_data = IMUDataWidget(app, self, self.connect_button_callback)
        # self.imu_data2 = IMUDataWidget(app, self, self.connect_button_callback, "copy")
        self.widget_added = False
        self.is_exerwatch = False
        self.is_selected = False
        self.is_connected = False
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
            dpg.add_text(tag=f"{self.panel_tag}_service_uuids", default_value=f"{self.data.service_uuids}")
            dpg.add_text(tag=f"{self.panel_tag}_service_data", default_value=f"{self.data.service_data}")
            dpg.add_text(tag=f"{self.panel_tag}_manufacturer_data", default_value=f"{self.data.manufacturer_data}")
            dpg.add_text(tag=f"{self.panel_tag}_platform_data", default_value=f"{self.data.platform_data}")
            dpg.add_text(tag=f"{self.panel_tag}_rssi", default_value=f"{self.data.rssi}")
            dpg.add_text(tag=f"{self.panel_tag}_services", default_value=f"{self.data.rssi}")

    def foldout_info(self, container: str = None):
        container = self.foldout_container if container is None else container
        with dpg.group(parent=container, filter_key=f"{self.device.name}", horizontal=True, tag=self.foldout_tag) as grp:
            dpg.add_button(tag=self.button_tag, label=f"Connect", callback=self.connect_button_callback, user_data=self.device, enabled=True, show=False)
            dpg.add_collapsing_header(label=f"{self.device.name} ({self.device.address})", tag=self.selectable_tag, closable=False, leaf=True)

        dpg.bind_item_handler_registry(self.selectable_tag, self.handler_registry)
        self.click_handler = dpg.add_item_clicked_handler(parent=self.handler_registry, callback=self.on_device_click)
        dpg.bind_item_theme(self.foldout_tag, self.themes.generic_device)

    def connect_button_callback(self, sender, app_data, device):
        print(f"Sender: {sender}")
        print(f"App Data: {app_data}")
        asyncio.run_coroutine_threadsafe(self.connect(device), self.app.bg_loop)

    def notification_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        dpg.set_item_label(self.selectable_tag, f"{self.device.name} ({self.device.address}) => {data.decode('utf-8')}")
        self.imu_data.update(data)
        # self.imu_data2.update(data)
        # print(f"{characteristic.description}: {data}")

    async def disconnect(self):
        await self.client.stop_notify(CHARACTERISTIC_UUID_TX)
        await self.client.disconnect()
        dpg.set_item_label(self.selectable_tag, f"{self.device.name} ({self.device.address})")
        dpg.configure_item(self.button_tag, label="Connect")

    async def connect(self, device):
        try:
            print(f"Connecting to {device.address}")
            await self.client.connect()
            self.is_connected = True
            dpg.configure_item(self.button_tag, label="Disconnect")
        except Exception as e:
            print(f"Exception connecting to device: {device}: {e}")
            return
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
            dpg.set_value(f"{self.panel_tag}_services", '\n - '.join(str_data))
        except Exception as e:
            print(f"Exception writing to gatt '{CHARACTERISTIC_UUID_RX}': {e}")
            
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
        self.widget_added = True

    def update(self, data: AdvertisementData):
        if data is None or self.is_exerwatch:
            return
        self.data = data
        self.is_exerwatch = any(map(lambda x: x.upper() in [EXER_BLE_SERVICE_UUID]+TEST_SERVICE_UUIDS, data.service_uuids))
        if self.is_exerwatch:
            self.update_theme()
            for i in range(len(self.app.devices.keys())):
                dpg.move_item_up(self.foldout_tag)  # Move ExerWatch sensors all the way to the top
            self.add_widget()
