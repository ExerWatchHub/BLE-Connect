import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import dearpygui_ext.themes as dpg_themes

COMPS = [dpg.mvInputText, dpg.mvButton, dpg.mvRadioButton, dpg.mvTabBar, dpg.mvTab, dpg.mvImage, dpg.mvMenuBar, dpg.mvViewportMenuBar, dpg.mvMenu, dpg.mvMenuItem, dpg.mvChildWindow, dpg.mvGroup, dpg.mvDragFloatMulti, dpg.mvSliderFloat, dpg.mvSliderInt, dpg.mvFilterSet, dpg.mvDragFloat, dpg.mvDragInt, dpg.mvInputFloat, dpg.mvInputInt, dpg.mvColorEdit, dpg.mvClipper, dpg.mvColorPicker, dpg.mvTooltip, dpg.mvCollapsingHeader, dpg.mvCombo, dpg.mvPlot, dpg.mvSimplePlot, dpg.mvDrawlist, dpg.mvWindowAppItem, dpg.mvSelectable, dpg.mvTreeNode, dpg.mvProgressBar, dpg.mvSpacer, dpg.mvImageButton, dpg.mvTimePicker, dpg.mvDatePicker, dpg.mvColorButton, dpg.mvFileDialog, dpg.mvTabButton, dpg.mvDrawNode, dpg.mvNodeEditor, dpg.mvNode, dpg.mvNodeAttribute, dpg.mvTable, dpg.mvTableColumn, dpg.mvTableRow]

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
                
        with dpg.theme() as global_theme:
            for comp_type in COMPS:
                with dpg.theme_component(comp_type, enabled_state=False):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (0.50 * 255, 0.50 * 255, 0.50 * 255, 1.00 * 255))
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 45, 48))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (45, 45, 48))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (45, 45, 48))
            dpg.bind_theme(global_theme)

