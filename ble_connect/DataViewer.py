import dearpygui.dearpygui as dpg
import os
import csv
import time
import datetime
import pandas as pd
import pickle as pkl
from icecream import ic
from .IMUData import *
from .GraphRegion import *
from .IMUDataWidget import IMUDataWidget
from .IMUDataPlot import *
from .config import FREQUENCY


class DataViewerWindow:
    total_widgets = 0

    def __init__(self, app, extra_id: str = ""):
        self.app = app
        self.themes = self.app.themes
        self.tag = f"data_viewer_window"
        self.file_dialog_id = f"file_dialog_id_{extra_id}"
        self.imu_widget = IMUDataWidget(app)
        self.make_window(self.tag)
        
    def show(self):
        dpg.show_item(self.tag)
        return self

    def ok_callback(self, sender, app_data):
        print("App Data: ", app_data)
        self.imu_widget.import_data(app_data['file_path_name'])

    def cancel_callback(self, sender, app_data):
        print('File dialog cancelled.')
        
    def make_window(self, tag):
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.ok_callback, cancel_callback=self.cancel_callback, id=self.file_dialog_id, width=700, height=400):
            dpg.add_file_extension("*.csv *.pkl *.json *.tsv){.csv,.pkl,.json,.tsv}", color=(0, 255, 255, 255), custom_text="[dataset]")
            dpg.add_file_extension(".py", color=(0, 255, 0, 255), custom_text="[Python]")

        with dpg.window(label="Viewer", tag=tag, menubar=True, autosize=True):
            dpg.bind_font(self.themes.body_font)
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Import Data", callback=lambda: dpg.show_item(self.file_dialog_id))
                    dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())
            self.imu_widget.add_widget(self.tag)
