from .BLEDeviceWidget import BLEDeviceWidget
from .DataViewer import DataViewerWindow
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
        dpg.configure_app(docking=True, docking_space=True, load_init_file="custom_layout.ini")  # must be called before create_viewport
        self.connected_device = None
        self.devices: dict[str, BLEDeviceWidget] = {}
        self.devices_list_id = "devices_list"
        self.device_info_tag = "devices_info"
        self.exer_sensors_table = "exer_sensors_table"
        self.exer_sensors_row = "exer_sensors_row"
        self.bg_loop = None
        self.scan_loading = "ble_scan_loading"
        self.filter_tag = "devices_filter"
        self.menubar = True
        self.stop_event = asyncio.Event()
        self.themes = None
        self.separate_sensors_windows = True
        self.graph_viewer : DataViewerWindow = None

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
        if not dpg.is_dearpygui_running():
            return
        if device.address not in self.devices:
            # print(f"New Device detected: {device}")
            device_ui = BLEDeviceWidget(self, device, data, self.filter_tag, self.device_info_tag, self.exer_sensors_row, self.separate_sensors_windows)
            device_ui.on_click = self.on_device_click
            self.devices[device.address] = device_ui
        self.devices[device.address].update(data)

    async def run(self):
        dpg.create_viewport(title="ExerWatch BLE-Connect", width=1000, height=800)
        dpg.setup_dearpygui()

        self.themes = BLEConnectTheme()
        self.make_devices_window("main_window", False)
        self.graph_viewer = DataViewerWindow(self).show()
        # dpg.show_debug()
        # dpg.show_item_registry()
        # self.run_scan(None)

        self.setup_bg_loop()
        dpg.show_viewport(maximized=True)

        # dpg.start_dearpygui()  # below replaces, start_dearpygui()
        while dpg.is_dearpygui_running():
            jobs = dpg.get_callback_queue()  # retrieves and clears queue
            dpg.run_callbacks(jobs)
            dpg.render_dearpygui_frame()
        dpg.destroy_context()

        self.bg_loop.call_soon_threadsafe(self.bg_loop.stop)
        
    
    def make_devices_window(self, tag, primary=True):
        with dpg.window(label="Devices", tag=tag, menubar=self.menubar, autosize=True):
            dpg.bind_font(self.themes.body_font)
            if self.menubar:
                with dpg.menu_bar():
                    with dpg.menu(label="File"):
                        dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())
                    with dpg.menu(label="View"):
                        dpg.add_menu_item(label="Save Layout", callback=lambda: dpg.save_init_file("custom_layout.ini"))
                        dpg.add_menu_item(label="Show Demo", callback=lambda: self.toggle_demo())
                    
            # self.exer_sensors_row = dpg.add_child_window(label="ExerWatch Sensors", no_close=False, no_collapse=False, autosize=True, pos=(0, 0))
            if not self.separate_sensors_windows:
                self.exer_sensors_row = dpg.add_window(label="ExerWatch Sensors", autosize=True)
                
            with dpg.group(horizontal=True) as grp:
                with dpg.child_window(tag=self.devices_list_id, height=600, width=600, resizable_x=True):
                    with dpg.group(horizontal=True):
                        dpg.add_loading_indicator(circle_count=5, tag=self.scan_loading, show=True, radius=2, color=(255, 255, 255, 255))
                        dpg.add_input_text(label="Name filter (inc, -exc)", user_data=self.filter_tag, callback=lambda sender, app_data, user_data: dpg.set_value(user_data, dpg.get_value(sender)))
                    dpg.add_filter_set(tag=self.filter_tag)
                with dpg.child_window(tag=self.device_info_tag, auto_resize_y=True, auto_resize_x=True, resizable_x=True, resizable_y=True):
                    dpg.add_text("Click on a device to see details")
        if primary:
            dpg.set_primary_window(tag, True)
        
    def toggle_debug(self):
        dpg.show_debug()
        
    def toggle_demo(self, collapsed=False):
        if not dpg.does_item_exist("__demo_id"):
            demo.show_demo()
        dpg.configure_item("__demo_id", collapsed=collapsed)
            
    def toggle_editors(self):
        dpg.show_style_editor()
        dpg.show_font_manager()