import dearpygui.dearpygui as dpg
import os
import csv
import time
import datetime
from icecream import ic


class IMUData:
    def __init__(self):
        self.x: list[float] = []
        self.y: list[float] = []
        self.z: list[float] = []
        self.t: list[float] = []
        self.region_idx = []

    def __len__(self):
        return len(self.x)

    def append(self, x: float = 0, y: float = 0, z: float = 0, t: float = None):
        self.x.append(x)
        self.y.append(y)
        self.z.append(z)
        if t is None or t < 0:
            self.t.append(len(self.t) + 1)
        else:
            self.t.append(t)


class IMUDataPlot:
    def __init__(self, parent, tag: str = "imu_plot", title="Time Series", area_selection_enabled=True):
        self.tag = tag
        self.parent = parent
        self.data: IMUData = IMUData()
        self.area_selection_enabled = area_selection_enabled
        self.title = title
        self.title_short = f"{self.title[0:3]}."
        self.drag_rect_tag = f"{self.tag}_drag_rect"
        self.plot_x = f"{self.tag}_plotX"
        self.plot_y = f"{self.tag}_plotY"
        self.plot_z = f"{self.tag}_plotZ"
        self.xaxis = f"{self.tag}_xaxis"
        self.yaxis = f"{self.tag}_yaxis"
        self.vline = f"{self.tag}_vline"
        self.hline = f"{self.tag}_hline"
        self.fit_checkbox_x = f"{self.tag}_fit_checkbox_x"
        self.fit_checkbox_y = f"{self.tag}_fit_checkbox_y"
        self.name_cell_width = 120
        self.show_data_table = False
        self.vlines = []
        self.region_idx = -1
        
    def reset(self):
        self.data = IMUData()
        dpg.configure_item(self.plot_x, x=[], y=[])
        dpg.configure_item(self.plot_y, x=[], y=[])
        dpg.configure_item(self.plot_z, x=[], y=[])
        
        try:
            dpg.configure_item(self.vline, x=[])
        except Exception as e:
            pass
        
        try:
            dpg.configure_item(self.hline, x=[])
        except Exception as e:
            pass
        
        if self.show_data_table:
            try:
                dpg.set_value(f"{self.tag}_table_x", "0.0")
                dpg.set_value(f"{self.tag}_table_y", "0.0")
                dpg.set_value(f"{self.tag}_table_z", "0.0")
            except Exception as e:
                pass
        
    def data_table(self, **table_kwargs):
        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=False, no_host_extendX=True, no_host_extendY=True, **table_kwargs):
            dpg.add_table_column(width=self.name_cell_width, width_fixed=True, width_stretch=False)
            dpg.add_table_column(width=self.name_cell_width, label=self.title_short, width_fixed=True, width_stretch=False)

            with dpg.table_row(label="X", height=20):
                dpg.add_text(default_value="X")
                dpg.add_text(tag=f"{self.tag}_table_x", default_value=f"0.0")

            with dpg.table_row(label="Y", height=20):
                dpg.add_text(default_value="Y")
                dpg.add_text(tag=f"{self.tag}_table_y", default_value=f"0.0")

            with dpg.table_row(label="Z", height=20):
                dpg.add_text(default_value="Z")
                dpg.add_text(tag=f"{self.tag}_table_z", default_value=f"0.0")
                
    def update_query_rect(self, query_rect=None):
        ymin, ymax = dpg.get_axis_limits(self.yaxis)
        if query_rect is None:
            query_rect = dpg.get_value(self.drag_rect_tag)
        xmin = query_rect[0]
        xmax = query_rect[2]
        dpg.set_value(self.drag_rect_tag, (xmin, ymin, xmax, ymax))
                
    def make_plot(self, width=-1, height=400, show_data_table=True, **plot_kwargs):
        self.show_data_table = show_data_table
        
        def query_handler(sender, query_rects, user_data):
            if self.area_selection_enabled:
                print(f"Query handler: {sender}, {query_rects}, {user_data}")
                self.parent.gyroscope.update_query_rect(query_rects[0])
                self.parent.accelerometer.update_query_rect(query_rects[0])
            
        def drag_rect_handler(*args, **kwargs):
            if self.area_selection_enabled:
                print(f"Drag rect handler: {args}, {kwargs}")
                # print(f"Plot drag handler: {s}_{self.tag}, {a}")
            
        with dpg.group(height=height, width=width) as grp:
            with dpg.group(horizontal=True, width=-1, height=-1, show=True):
                dpg.add_text("Auto-fit axes:")
                dpg.add_checkbox(label="X", tag=self.fit_checkbox_x, default_value=True)
                dpg.add_checkbox(label="Y", tag=self.fit_checkbox_y, default_value=True)
            with dpg.group(horizontal=self.show_data_table, width=-1, height=-1):
                if self.show_data_table:
                    self.data_table()
                with dpg.plot(label=self.title, query=True, vertical_mod=False, query_toggle_mod=False, box_select_mod=False, callback=query_handler, **plot_kwargs) as p:
                    if self.area_selection_enabled:
                        dpg.add_drag_rect(tag=self.drag_rect_tag, default_value=(0, 0, 0, 0), show=True, callback=lambda *args, **kwargs: drag_rect_handler(*args, **kwargs))
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, tag=self.xaxis, time=False)
                    dpg.add_plot_axis(dpg.mvYAxis, tag=self.yaxis)
                    dpg.add_line_series([], [], tag=self.plot_x, parent=self.xaxis, label="X")
                    dpg.add_line_series([], [], tag=self.plot_y, parent=self.xaxis, label="Y")
                    dpg.add_line_series([], [], tag=self.plot_z, parent=self.xaxis, label="Z")
                    try:
                        dpg.add_inf_line_series(self.vlines, tag=self.vline, parent=self.xaxis, label="Exercises boundaries", color=(255, 255, 255))
                    except Exception as e:
                        pass
                        # print(f"Exception adding vline: {e}.")
                        # print(e)

    def start_ex_region(self, before_padding=0):
        self.region_idx += 1
        # Add some "flat" data to separate exercise prototypes
        for i in range(before_padding):
            self.update(0, 0, 0)
        # print("STARTING EXERCISE AT: ", len(self.data))
        self.vlines.append(len(self.data))  # Start the region
        self.update_ex_region()

    def end_ex_region(self, after_padding=0):
        # print("ENDING EXERCISE AT: ", len(self.data))
        self.vlines.append(len(self.data))  # End the region
        # Add some "flat" data to separate exercise prototypes
        for i in range(after_padding):
            self.update(0, 0, 0)
        self.update_ex_region()
        
    def update_ex_region(self):
        try:
            dpg.configure_item(self.vline, x=self.vlines)
        except Exception as e:
            # print(f"Exception updating vline: {e}.")
            pass
            
    def update(self, x: float = 0, y: float = 0, z: float = 0, refresh_plot: bool = True):
        self.data.append(x, y, z)
        if refresh_plot:
            self.update_plot()
            if self.show_data_table:
                self.update_table()

    def update_table(self):
        if len(self.data) > 0:
            dpg.set_value(f"{self.tag}_table_x", f"{self.data.x[-1]:.2f}")
            dpg.set_value(f"{self.tag}_table_y", f"{self.data.y[-1]:.2f}")
            dpg.set_value(f"{self.tag}_table_z", f"{self.data.z[-1]:.2f}")
        
    def update_plot(self):
        dpg.configure_item(self.plot_x, x=self.data.t, y=self.data.x)
        dpg.configure_item(self.plot_y, x=self.data.t, y=self.data.y)
        dpg.configure_item(self.plot_z, x=self.data.t, y=self.data.z)
        
        if dpg.get_value(self.fit_checkbox_y):
            dpg.fit_axis_data(self.yaxis)
            self.update_query_rect()
        if dpg.get_value(self.fit_checkbox_x):
            dpg.fit_axis_data(self.xaxis)


class IMUDataWidget:
    total_widgets = 0

    def __init__(self, app, device_widget, connect_button_callback, extra_id: str = "", show_imu_table: bool = False):
        self.app = app
        self.themes = self.app.themes
        self.device_widget = device_widget
        self.device = device_widget.device
        self.connect_button_callback = connect_button_callback
        self.tag = f"{self.device.address}{extra_id}_imu_widget"
        self.float_cell_width = 50
        self.name_cell_width = 100
        self.btn_tag = f"{self.tag}_button"
        self.output_tag = f"{self.tag}_output"
        self.export_btn_tag = f"{self.tag}_export_button"
        self.clear_btn_tag = f"{self.tag}_clear_button"
        self.gyroscope: IMUDataPlot = IMUDataPlot(self, f"{self.tag}_gyro", "Gyroscope XYZ")
        self.accelerometer: IMUDataPlot = IMUDataPlot(self, f"{self.tag}_accelerometer", "Accelerometer XYZ")
        self.exercise_prototype: IMUDataPlot = IMUDataPlot(self, f"{self.tag}_ex_proto", "Exercise Prototype", area_selection_enabled=False)
        self.show_imu_table = show_imu_table
        self.exercise_counter = 0

    def add_widget(self, container: str = None, separate_window: bool = False):
        print(f"Adding IMU Widget to {container}")
        if separate_window:
            window = dpg.window(tag=self.tag, label=f"{self.device.name}", collapsed=False, width=1000, pos=(IMUDataWidget.total_widgets*20, IMUDataWidget.total_widgets*20))
            IMUDataWidget.total_widgets += 1
        else:
            window = dpg.child_window(tag=self.tag, auto_resize_y=True, parent=container)
        with window:
            with dpg.group(horizontal=True):
                dpg.add_text(tag=f"{self.tag}_title", default_value=f"{self.device.name}")
                dpg.add_text(tag=f"{self.tag}_address", default_value=f"{self.device.address}", wrap=500)
                dpg.bind_item_font(f"{self.tag}_title", self.themes.title_font)

            if self.show_imu_table:
                self.imu_table()

            with dpg.group(horizontal=True):
                dpg.add_button(tag=self.btn_tag, label="Connect", callback=self.connect_button_callback, user_data=self.device, enabled=True, show=True, width=100, height=30)
                dpg.add_button(tag=self.export_btn_tag, label="Export", callback=self.export_data, enabled=True, show=True, width=100, height=30)
                dpg.add_button(tag=self.clear_btn_tag, label="Clear", callback=self.clear_data, enabled=True, show=True, width=100, height=30)
                with dpg.group():
                    dpg.add_text(tag=f"{self.tag}_imu_string", default_value="IMU Data", wrap=500)
                    dpg.add_text(tag=f"{self.tag}_exported_string", default_value="Last export: None", wrap=500)
            with dpg.child_window(height=400, width=-1, show=True) as wo:
                dpg.bind_item_theme(wo, self.themes.exer_output_log)
                with dpg.group(horizontal=True, width=-1, height=-1) as go:
                    dpg.add_text(tag=self.output_tag, wrap=500, default_value="ExerSense Output:", show_label=False)
                    self.exercise_prototype.make_plot(show_data_table=False)

            self.gyroscope.make_plot()
            self.accelerometer.make_plot()


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
                
    def clear_data(self):
        self.accelerometer.reset()
        self.gyroscope.reset()
        self.exercise_prototype.reset()
        
    def export_data(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        file_time = datetime.datetime.now().strftime("%d-%m_%H-%M")
        imu_file_name = f"data/{self.device.name}_IMU_{file_time}.csv"
        print(f"Exporting imu data to: {imu_file_name}")
        with open(imu_file_name, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["time", "accel_x", "accel_y", "accel_z", "gyr_x", "gyr_y", "gyr_z"])
            for i in range(len(self.accelerometer.data)):
                row = [self.accelerometer.data.t[i]]
                row += [self.accelerometer.data.x[i], self.accelerometer.data.y[i], self.accelerometer.data.z[i]]
                row += [self.gyroscope.data.x[i], self.gyroscope.data.y[i], self.gyroscope.data.z[i]]
                csv_writer.writerow(row)
                
        proto_file_name = f"data/{self.device.name}_ExProto_{file_time}.csv"
        print(f"Exporting exercises prototype data to: {proto_file_name}")
        with open(proto_file_name, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["time", "x", "y", "z", "proto_id"])
            for i in range(len(self.exercise_prototype.data)):
                row = [self.accelerometer.data.t[i]]
                row += [self.accelerometer.data.x[i], self.accelerometer.data.y[i], self.accelerometer.data.z[i]]
                row += [self.gyroscope.data.x[i], self.gyroscope.data.y[i], self.gyroscope.data.z[i]]
                csv_writer.writerow(row)

        try:
            dpg.set_value(f"{self.tag}_exported_string", f"Last export: {imu_file_name} and {proto_file_name}")
        except Exception as e:
            pass
            

    def update(self, byte_data: bytearray, start_idx: int = 1):
        if self.device_widget.is_connected:
            dpg.configure_item(self.btn_tag, label="Disconnect")
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
            
            
    def run_exersense(self, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z):
        try:
            import exersens_learner
        except Exception as e:
            print(f"Exception importing exersens_learner: {e}")
            return
        # highlighted_region = dpg.get_value(self.drag_rect_tag)
        exer_out = exersens_learner.receive_data([(gyr_x, gyr_y, gyr_z)])
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
