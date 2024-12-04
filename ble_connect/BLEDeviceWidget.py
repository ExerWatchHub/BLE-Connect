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
from .config import EXER_BLE_SERVICE_UUID, CHARACTERISTIC_UUID_TX, CHARACTERISTIC_UUID_RX


class IMUDataWidget:
    def __init__(self, app, device_widget):
        self.app = app
        self.themes = self.app.themes
        self.fonts = self.app.fonts
        self.device_widget = device_widget
        self.device = device_widget.device
        self.tag = f"{self.device.address}_imu_widget"
        
    def add_widget(self, container: str):
        with dpg.group(parent=container, horizontal=True, tag=self.tag):
            dpg.add_text(tag=f"{self.tag}_title", default_value=self.device.name)
            dpg.add_button(tag=f"{self.tag}_button", label="Connect", callback=self.device_widget.connect_button_callback, user_data=self.device, enabled=True, show=True)
            dpg.bind_item_font(f"{self.tag}_title", self.fonts.title_font)
        dpg.add_text(parent=container, tag=f"{self.tag}_imu_string", default_value="IMU Data")
        with dpg.table(parent=container, header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=False):
            dpg.add_table_column()
            dpg.add_table_column(label="X")
            dpg.add_table_column(label="Y")
            dpg.add_table_column(label="Z")

            with dpg.table_row():
                dpg.add_text("Accl")
                dpg.add_input_float(tag=f"{self.tag}_accel_x", default_value=0.0, width=100, readonly=True, step=0)
                dpg.add_input_float(tag=f"{self.tag}_accel_y", default_value=0.0, width=100, readonly=True, step=0)
                dpg.add_input_float(tag=f"{self.tag}_accel_z", default_value=0.0, width=100, readonly=True, step=0)

            with dpg.table_row():
                dpg.add_text("Gyro")
                dpg.add_input_float(tag=f"{self.tag}_gyr_x", default_value=0.0, width=100, readonly=True, step=0)
                dpg.add_input_float(tag=f"{self.tag}_gyr_y", default_value=0.0, width=100, readonly=True, step=0)
                dpg.add_input_float(tag=f"{self.tag}_gyr_z", default_value=0.0, width=100, readonly=True, step=0)
    
    def update(self, byte_data: bytearray, start_idx: int = 1):
        if byte_data is not None:
            decoded = byte_data.decode('utf-8')
            data = [float(i) for i in decoded.split(",")]
            dpg.set_value(f"{self.tag}_imu_string", f"IMU Data: {decoded}")
            dpg.set_value(f"{self.tag}_accel_x", data[start_idx])
            dpg.set_value(f"{self.tag}_accel_y", data[start_idx+1])
            dpg.set_value(f"{self.tag}_accel_z", data[start_idx+2])
            dpg.set_value(f"{self.tag}_gyr_x", data[start_idx+3])
            dpg.set_value(f"{self.tag}_gyr_y", data[start_idx+4])
            dpg.set_value(f"{self.tag}_gyr_z", data[start_idx+5])


class BLEDeviceWidget:
    def __init__(self, app, device: BLEDevice, data: AdvertisementData = None, foldout_container: str = None, panel_container: str = None):
        self.app = app
        self.themes = self.app.themes
        self.fonts = self.app.fonts
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
        self.on_click = None
        self.handler_registry = dpg.add_item_handler_registry()
        self.click_handler = -1
        self.imu_data = IMUDataWidget(app, self)
        self.is_exerwatch = False
        self.is_selected = False
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

    def device_info(self, container: str):
        try:
            dpg.delete_item(container, children_only=True)
        except Exception as e:
            print(f"Exception deleting items: {e}")
        with dpg.group(parent=container, tag=self.panel_tag) as grp:
            self.imu_data.add_widget(grp)
            dpg.add_text(tag=f"{self.panel_tag}_address", default_value=f"{self.device.address}")
            dpg.add_text(tag=f"{self.panel_tag}_name", default_value=f"{self.device.name}")
            dpg.add_text(tag=f"{self.panel_tag}_service_uuids", default_value=f"{self.data.service_uuids}")
            dpg.add_text(tag=f"{self.panel_tag}_service_data", default_value=f"{self.data.service_data}")
            dpg.add_text(tag=f"{self.panel_tag}_manufacturer_data", default_value=f"{self.data.manufacturer_data}")
            dpg.add_text(tag=f"{self.panel_tag}_platform_data", default_value=f"{self.data.platform_data}")
            dpg.add_text(tag=f"{self.panel_tag}_rssi", default_value=f"{self.data.rssi}")
            dpg.add_text(tag=f"{self.panel_tag}_services", default_value=f"{self.data.rssi}")

    def foldout_info(self, container: str):
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
        dpg.set_item_label(self.selectable_tag, f"{self.device.name} ({self.device.address}) => {data.decode("utf-8")}")
        self.imu_data.update(data)
        # print(f"{characteristic.description}: {data}")

    async def disconnect(self):
        await self.client.stop_notify(CHARACTERISTIC_UUID_TX)
        await self.client.disconnect()
        dpg.set_item_label(self.selectable_tag, f"{self.device.name} ({self.device.address})")
        dpg.configure_item(self.button_tag, enabled=True)

    async def connect(self, device):
        try:
            print(f"Connecting to {device.address}")
            await self.client.connect()
        except Exception as e:
            print(f"Exception connecting to device: {device}: {e}")
            return
        dpg.configure_item(self.button_tag, enabled=False)
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

    def update(self, data: AdvertisementData):
        self.data = data
        if self.data is not None:
            if not self.is_exerwatch:
                self.is_exerwatch = any(map(lambda x: x.upper() == EXER_BLE_SERVICE_UUID, data.service_uuids))
                if self.is_exerwatch:
                    self.update_theme()
                    for i in range(len(self.app.devices.keys())):
                        dpg.move_item_up(self.foldout_tag)  # Move ExerWatch sensors all the way to the top
