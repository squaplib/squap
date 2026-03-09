"""
Optimisation
============

A way to experiment with the different optimisation options.
"""
import squap
from squap import var
import numpy as np


def update_data():
    var.x_lin = np.linspace(0, 1, var.N_points)


def update():
    if not var.pause:
        if squap.get_active_tab().name == "plot":
            y = np.random.random(var.N_points)
            curve.set_data(var.x_lin, y)
        else:
            x = np.random.random(var.N_points)
            y = np.random.random(var.N_points)
            curve.set_data(x, y)


def update_kwargs():
    if squap.get_active_tab().name == "plot":
        curve.set_data(width=var.width, antialias=var.antialias, color=var.color)
    if squap.get_active_tab().name == "scatter":
        curve.set_data(size=var.size, symbol_line_width=var.symbol_line_width, symbol_color=var.color, pixel_mode=var.pixel_mode)


def tab_changed():
    if squap.get_active_tab().name == "plot":
        print("current tab is plot")
        curve.set_data(w=var.width, s=-1)
    elif squap.get_active_tab().name == "scatter":
        print("current tab is scatter")
        curve.set_data(w=-1, s=var.size, symbol_line_width=var.symbol_line_width)


curve = squap.plot()

plot_tab = squap.add_tab("plot")
scatter_tab = squap.add_tab("scatter")

squap.add_color_picker("color", "y")[0].bind(update_kwargs)
squap.add_checkbox("autoscale", False)[0].bind(lambda: squap.enable_autoscale(enable=var.autoscale))
squap.add_checkbox("autopan", False)[0].bind(lambda: squap.enable_autopan(enable=var.autopan))
squap.add_checkbox("pause", False)
squap.add_inputbox("N_points", 50)[0].bind(update_data)
plot_tab.add_inputbox("width", 1, type_func=int).bind(update_kwargs)
plot_tab.add_checkbox("antialias", False).bind(update_kwargs)
scatter_tab.add_inputbox("size", 7).bind(update_kwargs)
scatter_tab.add_checkbox("pixel_mode", True).bind(update_kwargs)
scatter_tab.add_inputbox("symbol_line_width", 1).bind(update_kwargs)
# autopan only works if autoscale is turned on

squap.set_xlim(0, 1)
squap.set_ylim(0, 1)

update_data()
squap.on_refresh(update)
squap.display_fps()

squap.on_tab_change(tab_changed)

squap.show()
