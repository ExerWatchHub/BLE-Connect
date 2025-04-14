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
from .IMUDataPlot import *
from .config import FREQUENCY
from .SensorDevice import LocalFileMockDevice, SensorDevice
import importlib

def is_mock_device(device):
    return isinstance(device, LocalFileMockDevice)

class IMUDataWidget:
    total_widgets = 0

    def __init__(self, app, device=None, extra_id: str = "", show_imu_table: bool = False):
        self.app = app
        self.themes = self.app.themes
        self.device: SensorDevice = device if device is not None else LocalFileMockDevice()
        self.tag = f"{self.device.address}_imu_widget{extra_id}"
        self.float_cell_width = 50
        self.name_cell_width = 100
        self.connect_btn_tag = f"{self.tag}_conect_button"
        self.pause_btn_tag = f"{self.tag}_pause_button"
        self.output_tag = f"{self.tag}_output"
        self.export_btn_tag = f"{self.tag}_export_button"
        self.clear_btn_tag = f"{self.tag}_clear_button"
        self.detect_button = f"{self.tag}_detection"
        self.live_detect_checkbox = f"{self.tag}_live_detection"
        self.gyroscope: IMUDataPlot = IMUDataPlot(self, f"{self.tag}_gyro", "Gyroscope XYZ")
        self.accelerometer: IMUDataPlot = IMUDataPlot(self, f"{self.tag}_accelerometer", "Accelerometer XYZ")
        self.exercise_prototype: IMUDataPlot = IMUDataPlot(self, f"{self.tag}_ex_proto", "Exercise Prototype", area_selection_enabled=False)
        self.show_imu_table = show_imu_table
        self.exercise_counter = 0
        
    def device_info(self):
        with dpg.group(horizontal=True):
            dpg.add_text(tag=f"{self.tag}_title", default_value=f"{self.device.name}")
            dpg.add_text(tag=f"{self.tag}_address", default_value=f"{self.device.address}", wrap=500)
            dpg.bind_item_font(f"{self.tag}_title", self.themes.title_font)

        # Cannot connect or export data from a mock device!
        if is_mock_device(self.device):
            return
        
        if self.show_imu_table:
            self.imu_table()

        with dpg.group(horizontal=True):
            dpg.add_button(tag=self.connect_btn_tag, label="Connect", callback=self.device.toggle_connect, user_data=self.device, enabled=True, show=True, width=100, height=30)
            dpg.add_button(tag=self.pause_btn_tag, label="PAUSE", callback=self.toggle_processing, enabled=True, show=True, width=100, height=30)
            dpg.add_button(tag=self.export_btn_tag, label="Export", callback=self.export_data, enabled=True, show=True, width=100, height=30)
            dpg.add_button(tag=self.clear_btn_tag, label="Clear", callback=self.clear_data, enabled=True, show=True, width=100, height=30)
            with dpg.group():
                dpg.add_text(tag=f"{self.tag}_imu_string", default_value="IMU Data", wrap=500)
                dpg.add_text(tag=f"{self.tag}_exported_string", default_value="Last export: None", wrap=500)
                
                
    def add_widget(self, container: str = None, separate_window: bool = False):
        print(f"Adding IMU Widget to {container}")
        if separate_window:
            window = dpg.window(tag=self.tag, label=f"{self.device.name}", collapsed=False, max_size=(1900, 1200), min_size=(500, 500), width=1200, height=1500, no_resize=False, pos=(IMUDataWidget.total_widgets*20, IMUDataWidget.total_widgets*20))
            IMUDataWidget.total_widgets += 1
        else:
            window = dpg.child_window(tag=self.tag, auto_resize_y=True, autosize_y=True, parent=container)
        with window:
            self.device_info()
            with dpg.child_window(height=400, width=-1, show=True) as wo:
                dpg.bind_item_theme(wo, self.themes.exer_output_log)
                with dpg.group(horizontal=True, width=-1, height=-1) as go:
                    dpg.add_text(tag=self.output_tag, wrap=500, default_value="ExerSense Output:", show_label=False)
                    self.exercise_prototype.make_plot(show_data_table=False)

            with dpg.group(horizontal=True):
                dpg.add_button(tag=self.detect_button, label="Run Detection", callback=self.manual_detection, user_data=self.device, enabled=False, show=True, width=120, height=30)
                dpg.add_checkbox(label="Live Detection", tag=self.live_detect_checkbox, default_value=True)
                dpg.add_slider_float(tag=f"{self.tag}_linearity_slider", label="Linearity", default_value=0.2, max_value=1.0, min_value=0.1, width=100, height=30)
                dpg.add_slider_float(tag=f"{self.tag}_periodicty_slider", label="Periodicity", default_value=FREQUENCY/2, max_value=FREQUENCY, min_value=1.0, width=100, height=30)

            self.gyroscope.make_plot()
            self.accelerometer.make_plot()

    def manual_detection(self, sender, app_data):
        self.detect_prototype(reload_module=True)
        
    def imu_table(self):
        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchSame, no_host_extendX=True):
            dpg.add_table_column(width=self.name_cell_width)
            dpg.add_table_column(label="X")
            dpg.add_table_column(label="Y")
            dpg.add_table_column(label="Z")

            with dpg.table_row():
                dpg.add_text("Accl")
                dpg.add_text(tag=f"{self.tag}_accelerometer_x", default_value=f"0.0")
                dpg.add_text(tag=f"{self.tag}_accelerometer_y", default_value=f"0.0")
                dpg.add_text(tag=f"{self.tag}_accelerometer_z", default_value=f"0.0")

            with dpg.table_row():
                dpg.add_text("Gyro")
                dpg.add_text(tag=f"{self.tag}_gyr_x", default_value=f"0.0")
                dpg.add_text(tag=f"{self.tag}_gyr_y", default_value=f"0.0")
                dpg.add_text(tag=f"{self.tag}_gyr_z", default_value=f"0.0")
                
    def update_imu_table(self, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, imu_string):
        try:
            dpg.set_value(f"{self.tag}_imu_string", f"{imu_string}")
        except Exception as e:
            pass
        if not self.show_imu_table:
            return
        dpg.set_value(f"{self.tag}_accelerometer_x", f"{acc_x:.2f}")
        dpg.set_value(f"{self.tag}_accelerometer_y", f"{acc_y:.2f}")
        dpg.set_value(f"{self.tag}_accelerometer_z", f"{acc_z:.2f}")
        dpg.set_value(f"{self.tag}_gyr_x", f"{gyr_x:.2f}")
        dpg.set_value(f"{self.tag}_gyr_y", f"{gyr_y:.2f}")
        dpg.set_value(f"{self.tag}_gyr_z", f"{gyr_z:.2f}")
                
    def toggle_processing(self):
        if self.device.is_paused:
            self.device.is_paused = False
            dpg.configure_item(self.pause_btn_tag, label="PAUSE")
        else:
            self.device.is_paused = True
            dpg.configure_item(self.pause_btn_tag, label="RESUME")
            
    def clear_data(self):
        self.accelerometer.reset()
        self.gyroscope.reset()
        self.exercise_prototype.reset()

        # try:
        #     offset_cuts = [[0, -10, 10, 10], [15, -10, 25, 10], [30, -10, 70, 10]]
        #     self.gyroscope.update_cuts(offset_cuts)
        #     self.accelerometer.update_cuts(offset_cuts)
        # except Exception as e:
        #     raise e
        #     print(f"Exception updating region cuts: {e}")
        
        
    def import_data(self, file_path_name):
        print(f"Importing data from: {file_path_name}")
        
        
    def export_data(self, out_dir="data"):
        export_time = datetime.datetime.now().strftime("%d-%m_%H-%M")
        out_dir = f"{out_dir}/{export_time}"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        data = {}
        
        # IMU DATA EXPORT
        imu_columns = ["time", "accel_x", "accel_y", "accel_z", "gyr_x", "gyr_y", "gyr_z"]
        imu_df = pd.DataFrame(columns=imu_columns)
        imu_file_name = f"{out_dir}/{self.device.name}_IMU_{export_time}.csv"
        print(f"Exporting imu data to: {imu_file_name}")
        imu_df['time'] = self.accelerometer.data.t
        imu_df['accel_x'] = self.accelerometer.data.x
        imu_df['accel_y'] = self.accelerometer.data.y
        imu_df['accel_z'] = self.accelerometer.data.z
        imu_df['gyr_x'] = self.gyroscope.data.x
        imu_df['gyr_y'] = self.gyroscope.data.y
        imu_df['gyr_z'] = self.gyroscope.data.z
        imu_df.to_csv(imu_file_name, index=False)
        
        # Gyr and Accel CUTS/REGIONS export
        cuts_columns = ["xmin", "ymin", "xmax", "ymax"]
        cuts_file_name = f"{{out_dir}}/{self.device.name}_cuts_{export_time}.csv"
        cuts_df = pd.DataFrame(columns=cuts_columns)
        print(f"Exporting cuts/regions data to: {cuts_file_name}")
        for r in self.gyroscope.offset_cuts:
            cuts_df['xmin'] = r.xmin
            cuts_df['ymin'] = r.ymin
            cuts_df['xmax'] = r.xmax
            cuts_df['ymax'] = r.ymax
        cuts_df.to_csv(cuts_file_name, index=False)
                
        # Prototype data export
        proto_columns = ["time", "x", "y", "z", "w"]
        proto_file_name = f"{out_dir}/{self.device.name}_proto_{export_time}.csv"
        proto_df = pd.DataFrame(columns=proto_columns)
        print(f"Exporting exercises prototype data to: {proto_file_name}")
        proto_df['time'] = self.exercise_prototype.data.t
        proto_df['x'] = self.exercise_prototype.data.x
        proto_df['y'] = self.exercise_prototype.data.y
        proto_df['z'] = self.exercise_prototype.data.z
        proto_df['w'] = self.exercise_prototype.data.w
        proto_df.to_csv(proto_file_name, index=False)
        
        data['imu'] = imu_df
        data['cuts'] = cuts_df
        data['proto'] = proto_df
        pkl_export = f"{out_dir}/{self.device.name}_{export_time}.pkl"
        print(f"Exporting pickle data to: {pkl_export}")
        with open(pkl_export, "wb") as f:
            pkl.dump(data, f)

        try:
            dpg.set_value(f"{self.tag}_exported_string", f"Last export: {imu_file_name} and {proto_file_name}")
        except Exception as e:
            pass
        print("All exports completed!")
            
    def on_disconnect(self):
        dpg.configure_item(self.connect_btn_tag, label="Connect")
        dpg.configure_item(self.pause_btn_tag, label="PAUSE", enabled=False)

    def on_connect(self):
        dpg.configure_item(self.connect_btn_tag, label="Disconnect")
        dpg.configure_item(self.pause_btn_tag, label="PAUSE", enabled=True)

    def update(self, byte_data: bytearray, start_idx: int = 1):
        if self.device.is_paused:
            return
        if self.device.is_connected:
            dpg.configure_item(self.connect_btn_tag, label="Disconnect")
        if byte_data is None:
            print(f"IMU Data is None!")
            return 
        try:
            decoded = byte_data.decode('utf-8')
            data = [float(i) for i in decoded.split(",")]
            acc_x = data[start_idx]
            acc_y = data[start_idx+1]
            acc_z = data[start_idx+2]
            gyr_x = data[start_idx+3]
            gyr_y = data[start_idx+4]
            gyr_z = data[start_idx+5]
        except Exception as e:
            print(f"Exception decoding IMU data: {e}")
            return

        try:
            self.update_imu_table(acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, decoded)
        except Exception as e:
            print(f"Exception updating IMU TABLES with data: {e}")
        
        try:
            self.accelerometer.update(x=acc_x, y=acc_y, z=acc_z)
            self.gyroscope.update(x=gyr_x, y=gyr_y, z=gyr_z)
        except Exception as e:
            print(f"Exception updating IMU PLOTS with data: {e}")
        self.run_exersense(acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z)
        
    def detect_prototype(self, reload_module=True):
        try:
            import exersense.exersense_offline as learner
            if reload_module:
                importlib.reload(learner)
        except Exception as e:
            print(f"Exception importing exersense_learner: {e}")
            return
        gyr_region = dpg.get_value(self.gyroscope.drag_rect_tag)
        acc_region = dpg.get_value(self.accelerometer.drag_rect_tag)
        print(f"Detecting prototype from region. Gyr: [{gyr_region[0]}, {gyr_region[2]}], Acc: [{acc_region[0]}, {acc_region[2]}]")
        linearity_threshold = dpg.get_value(f"{self.tag}_linearity_slider")
        periodicity_threshold = dpg.get_value(f"{self.tag}_periodicty_slider")
        try:
            cuts, prototype_vector = learner.detect_prototype(gyr_region[0], gyr_region[2], linearity_threshold, periodicity_threshold)
            offset_cuts_gyr = []
            offset_cuts_acc = []
            if cuts is not None:
                for i in range(len(cuts)-1):
                    offset_cuts_gyr.append([cuts[i], gyr_region[1], cuts[i+1], gyr_region[3]])
                    offset_cuts_acc.append([cuts[i], acc_region[1], cuts[i+1], acc_region[3]])
                print(f"ExerSense Prototype Output: {offset_cuts_gyr}")
                self.gyroscope.update_cuts(offset_cuts_gyr)
                self.accelerometer.update_cuts(offset_cuts_acc)
                
            if prototype_vector is not None:
                for v in prototype_vector:
                    self.exercise_prototype.update(
                        x=v[0],
                        y=v[1],
                        z=v[2],
                        w=v[3]
                    )
            self.export_data()
        except Exception as e:
            print(f"Exception running exersense: {e}")
            raise e
            
    def run_exersense(self, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z):
        try:
            import exersense.exersense_online as tracker
        except Exception as e:
            print(f"Exception importing exersense tracker: {e}")
            return
        try:
            exer_out = tracker.receive_data([(gyr_x, gyr_y, gyr_z)], [(acc_x, acc_y, acc_z)], [.1])
        except Exception as e:
            print(f"Exception running exersense: {e}")
            return
        prefix = f"\n  -"
        if exer_out is not None and len(exer_out) > 0:
            out_type = exer_out[0].lower()
            out_print = f"\n[Ex.{self.exercise_counter+1}] "
            # Exercise region 'S'tart
            if out_type == 's':
                start_off_x, start_off_y, start_off_z = exer_out[1] # it's a tuple
                reps = exer_out[2]
                reps_roms = ""
                for rom in exer_out[3]:
                    reps_roms = f"{prefix} Rep accuracy: {rom[0]:.2f}, Max ROM XYZ: [{rom[1]:.2f}, {rom[2]:.2f}, {rom[3]:.2f}]"

                dominant_axis_idx = exer_out[4]
                self.exercise_prototype.start_ex_region()
                self.accelerometer.start_ex_region()
                self.gyroscope.start_ex_region()
                
                prototype_dom_axis = []
                prototype_vector = exer_out[5]
                for v in prototype_vector:
                    prototype_dom_axis.append(float(v))
                    # Only add the prototype value to the dominant axis
                    self.exercise_prototype.update(
                        x = v if dominant_axis_idx==0 else 0,
                        y = v if dominant_axis_idx==1 else 0,
                        z = v if dominant_axis_idx==2 else 0
                    )
                out_print += f"START -  Reps={reps}"
                out_print += f"{prefix} Offsets XYZ: [{start_off_x}, {start_off_y}, {start_off_z}]"
                out_print += reps_roms
                out_print += f"{prefix} Dominant axis: {dominant_axis_idx} - Prototype XYZ: {prototype_dom_axis}"
            elif out_type == 'u':
                # Exercise 'U'pdate
                reps = exer_out[1]
                roms = ""
                for axis_rom_data in exer_out[2]:
                    rep_correctness = axis_rom_data[0]
                    rom_x = axis_rom_data[1]
                    rom_y = axis_rom_data[2]
                    rom_z = axis_rom_data[3]
                    roms += f"({rep_correctness:.2f}, {rom_x:.2f}, {rom_y:.2f}, {rom_z:.2f}) "
                out_print += f"UPDATE - Reps={reps}, ROMs: {roms}"
            elif out_type == 'e':
                # Exercise region 'E'nd
                end_off_x, end_off_y, end_off_z = exer_out[1]
                out_print += f"END - Exercise XYZ: [{end_off_x}, {end_off_y}, {end_off_z}]\n"
                self.exercise_prototype.end_ex_region(after_padding=5)
                self.accelerometer.end_ex_region()
                self.gyroscope.end_ex_region()
                self.exercise_counter += 1
            else:
                out_print = "Unknown output type!"

            dpg.set_value(self.output_tag, dpg.get_value(self.output_tag)+f"{out_print}")
            # try:
            #     print(dpg.get_y_scroll(self.output_tag))
            # except Exception as e:
            #     print(f"Exception getting y scroll: {e}")
            print(f"ExerSens Output: {exer_out}")
