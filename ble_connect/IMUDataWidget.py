import dearpygui.dearpygui as dpg

class IMUDataWidget:
    def __init__(self, app, device_widget, connect_button_callback, extra_id: str = ""):
        self.app = app
        self.themes = self.app.themes
        self.device_widget = device_widget
        self.device = device_widget.device
        self.connect_button_callback = connect_button_callback
        self.tag = f"{self.device.address}{extra_id}_imu_widget"
        self.float_cell_width = 50
        self.name_cell_width = 100
        self.btn_tag = f"{self.tag}_button"

    def add_widget(self, container: str):
        print(f"Adding IMU Widget to {container}")
        with dpg.child_window(parent=container, tag=self.tag, auto_resize_y=True, auto_resize_x=True):
            with dpg.group(horizontal=True):
                dpg.add_text(tag=f"{self.tag}_title", default_value=self.device.name)
                dpg.add_button(tag=self.btn_tag, label="Connect", callback=self.connect_button_callback, user_data=self.device, enabled=True, show=True)
                dpg.bind_item_font(f"{self.tag}_title", self.themes.title_font)
            dpg.add_text(tag=f"{self.tag}_imu_string", default_value="IMU Data", wrap=200)
            with dpg.table(header_row=True,
                           borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True,
                           policy=dpg.mvTable_SizingFixedFit, no_host_extendX=True):
                dpg.add_table_column(width=self.name_cell_width)
                dpg.add_table_column(label="X")
                dpg.add_table_column(label="Y")
                dpg.add_table_column(label="Z")

                with dpg.table_row():
                    dpg.add_text("Accl")
                    dpg.add_input_float(tag=f"{self.tag}_accel_x", default_value=0.0, readonly=True, step=0, width=self.float_cell_width)
                    dpg.add_input_float(tag=f"{self.tag}_accel_y", default_value=0.0, readonly=True, step=0, width=self.float_cell_width)
                    dpg.add_input_float(tag=f"{self.tag}_accel_z", default_value=0.0, readonly=True, step=0, width=self.float_cell_width)

                with dpg.table_row():
                    dpg.add_text("Gyro")
                    dpg.add_input_float(tag=f"{self.tag}_gyr_x", default_value=0.0, readonly=True, step=0, width=self.float_cell_width)
                    dpg.add_input_float(tag=f"{self.tag}_gyr_y", default_value=0.0, readonly=True, step=0, width=self.float_cell_width)
                    dpg.add_input_float(tag=f"{self.tag}_gyr_z", default_value=0.0, readonly=True, step=0, width=self.float_cell_width)

    def update(self, byte_data: bytearray, start_idx: int = 1):
        if self.device_widget.is_connected:
            dpg.configure_item(self.btn_tag, label="Disconnect")
        if byte_data is not None:
            try:
                decoded = byte_data.decode('utf-8')
                data = [float(i) for i in decoded.split(",")]
                dpg.set_value(f"{self.tag}_imu_string", f"IMU Data: {decoded}")
                dpg.set_value(f"{self.tag}_accel_x", data[start_idx])
                dpg.set_value(f"{self.tag}_accel_y", data[start_idx+1])
                dpg.set_value(f"{self.tag}_accel_z", data[start_idx+2])
                dpg.set_value(f"{self.tag}_gyr_x", data[start_idx+3])
                dpg.set_value(f"{self.tag}_gyr_y", data[start_idx+4])
                dpg.set_value(f"{self.tag}_gyr_z", data[start_idx+5])
            except Exception as e:
                print(f"Exception decoding IMU data: {e}")
