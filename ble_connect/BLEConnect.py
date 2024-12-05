from .BLEDeviceWidget import BLEDeviceWidget
from .themes import BLEConnectTheme
from bleak import BleakClient, BleakScanner, BLEDevice, AdvertisementData
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import dearpygui_ext.themes as dpg_themes
import logging
import argparse
from threading import Thread
import asyncio


class BLEConnect:
    def __init__(self):
        dpg.create_context()
        self.connected_device = None
        self.devices: dict[str, BLEDeviceWidget] = {}
        self.devices_list_id = dpg.generate_uuid()
        self.device_info_tag = dpg.generate_uuid()
        self.exer_sensors_table = dpg.generate_uuid()
        self.exer_sensors_row = dpg.generate_uuid()
        self.bg_loop = None
        self.scan_loading = "ble_scan_loading"
        self.filter_tag = "devices_filter"
        self.menubar = False
        self.stop_event = asyncio.Event()
        self.themes = None

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
        
    def on_device_click(self, sender, app_data, device):
        for d in self.devices.values():
            d.set_selected(d.click_handler == sender)

    def on_device_detected(self, device: BLEDevice, data: AdvertisementData):
        # print(f"Device detected: {device}")
        if device.address not in self.devices:
            device_ui = BLEDeviceWidget(self, device, data, self.filter_tag, self.device_info_tag, self.exer_sensors_row)
            device_ui.on_click = self.on_device_click
            self.devices[device.address] = device_ui
        self.devices[device.address].update(data)

    async def run(self):
        dpg.create_viewport()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self.themes = BLEConnectTheme()

        # demo.show_demo()
        # dpg.configure_item("__demo_id", collapsed=True)
        # dpg.show_style_editor()
        # dpg.show_font_manager()
        
        self.make_window("main_window")
        self.setup_bg_loop()
        # self.run_scan(None)

        dpg.start_dearpygui()
        dpg.destroy_context()

        self.bg_loop.call_soon_threadsafe(self.bg_loop.stop)


    def make_window(self, tag):
        with dpg.window(label="Example Window", tag=tag, autosize=True, menubar=self.menubar):
            dpg.bind_font(self.themes.body_font)
            if self.menubar:
                with dpg.menu_bar():
                    dpg.add_menu(label="Menu Options")
                    
            with dpg.table(tag=self.exer_sensors_table, header_row=False, borders_innerH=True, borders_outerH=False, borders_innerV=True, borders_outerV=False, resizable=False):
                dpg.add_table_column()
                dpg.table_row(tag=self.exer_sensors_row)

            with dpg.table(header_row=False, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True):
                dpg.add_table_column()
                dpg.add_table_column()

                with dpg.table_row():
                    self.devices_list()
                    self.device_details()
        dpg.set_primary_window(tag, True)

    def devices_list(self):
        with dpg.group():
            with dpg.group(horizontal=True):
                dpg.add_loading_indicator(circle_count=5, tag=self.scan_loading, show=True, radius=2, color=(255, 255, 255, 255))
                dpg.add_input_text(label="Name filter (inc, -exc)", user_data=self.filter_tag, callback=lambda sender, app_data, user_data: dpg.set_value(user_data, dpg.get_value(sender)))
            with dpg.child_window(tag=self.devices_list_id, auto_resize_y=True):
                dpg.add_filter_set(tag=self.filter_tag)

    def device_details(self):
        with dpg.group(tag=self.device_info_tag):
            dpg.add_text("Click on a device to see details")
