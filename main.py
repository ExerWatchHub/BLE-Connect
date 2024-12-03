

import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import asyncio
import ble_scanner
import ble_notifications


dpg.create_context()

table_uuid = dpg.generate_uuid()

def save_callback():
    print("Save Clicked")
    

def ui_test():
    dpg.add_text("Hello world")
    dpg.add_button(label="Save", callback=save_callback)
    dpg.add_input_text(label="string")
    dpg.add_slider_float(label="float")
    

def connect_to_device(sender, app_data, device):
    print(f"Sender: {sender}")
    print(f"App Data: {app_data}")
    try:
        print(f"Connecting to {device.address}")
    except Exception as e:
        print(f"Error printing device address: {e}")
    
    
def scan_callback(sender):
    global table_uuid
    devices = asyncio.run(ble_scanner.scan())
    try:
        dpg.delete_item(table_uuid, children_only=True)
    except Exception as e:
        pass
    dpg.add_table_column(label="id", parent=table_uuid)
    dpg.add_table_column(label="Address", parent=table_uuid)
    dpg.add_table_column(label="Name", parent=table_uuid)
    dpg.add_table_column(label="Connect", parent=table_uuid)
    for i, d in enumerate(devices):
        row_id = f"{table_uuid}_row_{i}"
        dpg.add_table_row(filter_key=f"Cell {i}, 1", parent=table_uuid, tag=row_id)
        dpg.add_input_int(label=" ", step=0, parent=row_id)
        dpg.add_text(f"{d.address}", parent=row_id)
        dpg.add_text(f"{d.name}", parent=row_id)
        dpg.add_button(label=f"Connect", parent=row_id, callback=connect_to_device, user_data=d)


def ui_table():
    global table_uuid
    # with filtering
    dpg.add_button(label="Scan", callback=scan_callback)
    dpg.add_text("Using Filter (column 3)")
    table_uuid = dpg.generate_uuid()
    dpg.add_input_text(label="Filter (inc, -exc)", user_data=table_uuid, callback=lambda s, a, u: dpg.set_value(u, dpg.get_value(s)))
    with dpg.table(header_row=True, no_host_extendX=True, delay_search=True,
                   borders_innerH=True, borders_outerH=True, borders_innerV=True,
                   borders_outerV=True, context_menu_in_body=True, row_background=True,
                   policy=dpg.mvTable_SizingFixedFit,
                   scrollY=True, tag=table_uuid) as table_id:
        dpg.add_checkbox(label="resizable", before=table_id, default_value=True, user_data=table_id, callback=lambda sender, app_data, user_data: dpg.configure_item(user_data, resizable=app_data))
    

def make_ui():
    # demo.show_demo()
    with dpg.window(label="Example Window", width=800, height=500):
        # ui_test()
        ui_table()
        

ble_scanner.main()
make_ui()


dpg.create_viewport()
dpg.setup_dearpygui()
dpg.show_viewport()
# below replaces, start_dearpygui()
while dpg.is_dearpygui_running():
    # insert here any code you would like to run in the render loop you can manually stop by using stop_dearpygui()
    dpg.render_dearpygui_frame()
    
dpg.destroy_context()
