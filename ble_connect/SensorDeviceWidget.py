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
from .IMUDataWidget import IMUDataWidget
from .config import EXER_BLE_SERVICE_UUID, EXER_CHARACTERISTIC_UUID_TX, EXER_CHARACTERISTIC_UUID_RX, WATCH_CHARACTERISTIC_UUID_RX, WATCH_CHARACTERISTIC_UUID_TX, TEST_SERVICE_UUIDS, FILTERED_DEVICES, AUTO_CONNECT
from .SensorDevice import SensorDevice

class SensorDeviceWidget:
    def __init__(self, app, device: SensorDevice, foldout_container: str = None, panel_container: str = None, exer_sensors_container: str = None, separate_window: bool = True):
        self.app = app
        self.themes = self.app.themes
        self.theme = self.themes.generic_device
        self.foldout_tag = f"{device.address}_foldout"
        self.selectable_tag = f"{device.address}_selectable"
        self.panel_tag = f"{device.address}_panel"
        self.button_tag = f"{device.address}_button"
        self.device: SensorDevice = device
        self.foldout_container = foldout_container
        self.panel_container = panel_container
        self.exer_sensors_container = exer_sensors_container
        self.on_click = None
        self.handler_registry = dpg.add_item_handler_registry()
        self.click_handler = -1
        self.imu_widget = IMUDataWidget(app, self.device)
        self.separate_window = separate_window
        if self.foldout_container is not None:
            self.foldout_info(self.foldout_container)

    def set_selected(self, selected: bool):
        self.device.is_selected = selected
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
            dpg.add_text(tag=f"{self.panel_tag}_service_data", default_value=f"{self.device.ad_data.service_data}")
            dpg.add_text(tag=f"{self.panel_tag}_manufacturer_data", default_value=f"{self.device.ad_data.manufacturer_data}")
            dpg.add_text(tag=f"{self.panel_tag}_platform_data", default_value=f"{self.device.ad_data.platform_data}")
            dpg.add_text(tag=f"{self.panel_tag}_rssi", default_value=f"{self.device.ad_data.rssi}")
            dpg.add_text(tag=f"{self.panel_tag}_services", default_value=f"{self.device.ad_data.rssi}")

    def foldout_info(self, container: str = None):
        container = self.foldout_container if container is None else container
        with dpg.group(parent=container, filter_key=f"{self.device.name}", horizontal=True, tag=self.foldout_tag) as grp:
            dpg.add_button(tag=self.button_tag, label=f"Connect", callback=self.device.toggle_connect, user_data=self.device, enabled=True, show=False)
            dpg.add_collapsing_header(label=f"{self.device.name} ({self.device.address})", tag=self.selectable_tag, closable=False, leaf=True)

        dpg.bind_item_handler_registry(self.selectable_tag, self.handler_registry)
        self.click_handler = dpg.add_item_clicked_handler(parent=self.handler_registry, callback=self.on_device_click)
        dpg.bind_item_theme(self.foldout_tag, self.themes.generic_device)

    def on_notification(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        # print(f"Notification received from {characteristic}: {data}")
        dpg.set_item_label(self.selectable_tag, f"{self.device.name} ({self.device.address}) => {data.decode('utf-8')}")
        self.imu_widget.update(data)
        # self.imu_widget2.update(data)
        # print(f"{characteristic.description}: {data}")
        
    def on_accepted_device(self):
        self.update_theme()
        for i in range(len(self.app.devices.keys())):
            dpg.move_item_up(self.foldout_tag)  # Move ExerWatch sensors all the way to the top
        self.add_widget()

    def update_theme(self):
        # dpg.configure_item(self.selectable_tag, selected=self.device.is_selected)
        self.theme = self.themes.generic_device
        if self.device.is_selected:
            self.theme = self.themes.selected_device
        elif self.device.is_exerwatch:
            self.theme = self.themes.exer_device
        # print(f"Updating theme for {self.device.name}: {self.theme} ")
        dpg.bind_item_theme(self.foldout_tag, self.theme)
        dpg.configure_item(self.button_tag, show=self.device.is_exerwatch)

    def add_widget(self, container: str = None):
        container = self.exer_sensors_container if container is None else container
        self.imu_widget.add_widget(self.exer_sensors_container, separate_window=self.separate_window)
        # self.imu_widget2.add_widget(self.exer_sensors_container)

    def on_disconnect(self):
        dpg.configure_item(self.button_tag, label="Connect")
        dpg.set_item_label(self.selectable_tag, f"{self.device.name} ({self.device.address})")
        self.imu_widget.on_disconnect()

    def on_connect(self):
        dpg.configure_item(self.button_tag, label="Disconnect")
        self.imu_widget.on_connect()
        
    def on_services_discovered(self, characteristics, descriptors):
        str_data = ""
        if characteristics is not None:
            str_data = list(map(lambda x: f"{x.uuid}: {x.description}", characteristics.values()))
        if descriptors is not None:
            str_data += list(map(lambda x: f"{x.uuid}: {x.description}", descriptors.values()))
        dpg.set_value(f"{self.panel_tag}_services", '\n - '.join(str_data))
        
        
