import dearpygui.dearpygui as dpg
import os
import csv
import time
import datetime
from icecream import ic
from .IMUData import *
from .GraphRegion import *

class IMUDataPlot:
    def __init__(self, parent, tag: str = "imu_plot", title="Time Series", area_selection_enabled=True):
        self.tag = tag
        self.parent = parent
        self.data: IMUData = IMUData()
        self.area_selection_enabled = area_selection_enabled
        self.title = title
        self.title_short = f"{self.title[0:3]}."
        self.plot_areas_tag = f"{self.tag}_areas"
        self.drag_rect_tag = f"{self.tag}_drag_rect"
        self.plot_tag = f"{self.tag}_plot"
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
        self.offset_cuts: list[GraphRegion] = []

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

    def update_cuts(self, new_cuts):
        if len(new_cuts) <= 0:
            return
        for i, c in enumerate(new_cuts):
            if i < len(self.offset_cuts):
                print(f"Updating cut {i}: {c}")
                self.offset_cuts[i].update(region=c)
                self.offset_cuts[i].show()
            else:
                self.offset_cuts.append(GraphRegion(self, len(self.offset_cuts), c))
            
        if len(new_cuts) < len(self.offset_cuts):
            for i in range(len(new_cuts), len(self.offset_cuts)):
                self.offset_cuts[i].hide()
                
        for c in self.offset_cuts:
            c.hide()
        
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
                self.parent.detect_prototype()

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
                with dpg.plot(tag=self.plot_tag, label=self.title, query=True, vertical_mod=False, query_toggle_mod=False, box_select_mod=False, callback=query_handler, **plot_kwargs):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, tag=self.xaxis, time=False)
                    dpg.add_plot_axis(dpg.mvYAxis, tag=self.yaxis)
                    dpg.add_line_series([], [], tag=self.plot_x, parent=self.xaxis, label="X")
                    dpg.add_line_series([], [], tag=self.plot_y, parent=self.xaxis, label="Y")
                    dpg.add_line_series([], [], tag=self.plot_z, parent=self.xaxis, label="Z")
                    with dpg.draw_layer(tag=self.plot_areas_tag, parent=self.plot_tag):
                        print(f"Adding draw layer rect: {self.plot_areas_tag}")
                        pass
                    
                    if self.area_selection_enabled:
                        print(f"Adding drag rect: {self.drag_rect_tag}")
                        dpg.add_drag_rect(parent=self.plot_tag, tag=self.drag_rect_tag, default_value=(-10, 10), color=[255,0,0, 255], show=False, label="Selected Area")
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
