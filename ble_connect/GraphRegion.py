import dearpygui.dearpygui as dpg

class GraphRegion:
    def __init__(self, parent, region_idx, region=None):
        self.parent = parent
        self.id: str = f"{parent.plot_areas_tag}_region_{region_idx}"
        self.xmin: float = 0
        self.xmax: float = 0
        self.ymin: float = 0
        self.ymax: float = 0
        self.added = False
        self.update_extents(region=region)
        print(f"Adding new region cut {self.id}: [{self.xmin}, {self.ymin}, {self.xmax}, {self.ymax}]")
        color = (0, 0, 100, 100) if region_idx % 2 == 0 else (0, 0, 255, 100)
        dpg.draw_rectangle(pmin=(self.xmin, self.ymin), pmax=(self.xmax, self.ymax), fill=color, color=color, thickness=0.01, parent=parent.plot_areas_tag)
        self.added = True
        self.update_drag_rect()

    def update_extents(self, xmin=None, xmax=None, ymin=None, ymax=None, region=None):
        if region is not None:
            if isinstance(region, GraphRegion):
                self.xmin = region.xmin
                self.ymin = region.ymin
                self.xmax = region.xmax
                self.ymax = region.ymax
            elif len(region) >= 4:
                self.xmin = region[0]
                self.ymin = region[1]
                self.xmax = region[2]
                self.ymax = region[3]
            else:
                # only x values
                self.xmax = region[0]
                self.xmin = region[1]
        else:
            if xmin is not None:
                self.xmin = xmin
            if xmax is not None:
                self.xmax = xmax
            if ymin is not None:
                self.ymin = ymin
            if ymax is not None:
                self.ymax = ymax

    def update_drag_rect(self):
        return
        if self.added:
            dpg.set_value(self.id, (self.xmin, self.ymin, self.xmax, self.ymax))
            self.parent.update_plot()

    def update(self, **kwargs):
        self.update_extents(**kwargs)
        self.update_drag_rect()

    def show(self):
        return
        if self.added:
            dpg.show_item(self.id)

    def hide(self):
        return
        if self.added:
            dpg.hide_item(self.id)
