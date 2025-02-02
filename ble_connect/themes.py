import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import dearpygui_ext.themes as dpg_themes


class BLEConnectTheme:
    def __init__(self):
        with dpg.font_registry():
            self.title_font = dpg.add_font("assets/FiraCode-Regular.ttf", 20)
            self.body_font = dpg.add_font("assets/FiraCode-Regular.ttf", 14)
        self.generic_device: str = "generic_device"
        with dpg.theme(tag=self.generic_device):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)

        self.selected_device: str = "selected_device"
        with dpg.theme(tag=self.selected_device):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (0, 119, 200, 153))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (0, 119, 200, 153))

        self.exer_device: str = "exer_device"
        with dpg.theme(tag=self.exer_device):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (101, 66, 52))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (101, 66, 52))
                # dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (101, 66, 52))
                # dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (101, 66, 52))

        self.exer_output_log: str = "exer_output_log"
        with dpg.theme(tag=self.exer_output_log):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (17, 21, 38), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (17, 21, 38), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (17, 21, 38), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Header, (17, 21, 38), category=dpg.mvThemeCat_Core)
        
