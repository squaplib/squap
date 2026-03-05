"""
Plot Customisation
==================

Shows all plot customisation options.
As of yet incomplete.
"""
import squap
from squap import var
import numpy as np


def set_curve_data():
    x = np.linspace(var.min_x, var.max_x, var.Nx)
    y = eval(var.y_func)

    curve.set_data(x, y)


def set_err_data():
    x = np.linspace(var.min_x, var.max_x, var.Nx)
    y = eval(var.y_func)
    if var.x_err_type == "absolute":
        x_err = var.x_err
    else:
        x_err = var.x_err*x
    if var.y_err_type == "absolute":
        y_err = var.y_err
    else:
        y_err = var.y_err*y
    curve.set_data(x_err=x_err, y_err=y_err)


data_tab = squap.add_tab("data")
plot_tab = squap.add_tab("plot")
scatter_tab = squap.add_tab("scatter")
errorbar_tab = squap.add_tab("errorbar")
squap.set_active_tab("plot")

data_tab.add_inputbox("Nx", 40).bind(set_curve_data)
data_tab.add_inputbox("min_x", 0).bind(set_curve_data)
data_tab.add_inputbox("max_x", np.round(2*np.pi, 3)).bind(set_curve_data)
data_tab.add_inputbox("y_func", "np.sin(x)").bind(set_curve_data)

plot_boxes = [
    plot_tab.add_color_picker("color", "y"),
    plot_tab.add_inputbox("width", 1, type_func=int),
    plot_tab.add_checkbox("dashed", False),
    plot_tab.add_inputbox("dash_pattern", [16, 16]),
    plot_tab.add_dropdown("connect", ["all", "pairs", "finite", "auto"], 3),        # todo: allow custom option
    plot_tab.add_inputbox("gradient", ""),
    plot_tab.add_inputbox("downsample", 1, type_func=int),
    plot_tab.add_dropdown("downsample_method", ["subsample", "mean", "peak"], 1),
    plot_tab.add_checkbox("auto_downsample", False),
    plot_tab.add_checkbox("antialias", False),
    plot_tab.add_checkbox("skip_finite_check", False)

]

scatter_boxes = [
    scatter_tab.add_color_picker("symbol_color", "r"),
    scatter_tab.add_inputbox("size", -1),
    scatter_tab.add_inputbox("symbol_line_width", -1),
    scatter_tab.add_color_picker("symbol_line_color", "b"),
    scatter_tab.add_checkbox("pixel_mode", True)

]

errorbar_boxes = [
    errorbar_tab.add_inputbox("beam_size", 0),
    errorbar_tab.add_color_picker("errorbar_color", "g"),
    errorbar_tab.add_inputbox("errorbar_width", -1, type_func=int)

]
error_func_boxes = [
    errorbar_tab.add_inputbox("x_err", 0),
    errorbar_tab.add_dropdown("x_err_type", ["absolute", "relative"], 0),
    errorbar_tab.add_inputbox("y_err", 0),
    errorbar_tab.add_dropdown("y_err_type", ["absolute", "relative"], 0),
]
for box in error_func_boxes:
    box.bind(set_err_data)

all_boxes = plot_boxes + scatter_boxes + errorbar_boxes

for box in all_boxes:
    def update_this_box(box_=box):
        curve.set_data(**{box_.current_name: box_.value()})

    box.bind(update_this_box)


curve = squap.plot()
set_curve_data()
squap.show()
