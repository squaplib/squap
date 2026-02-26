# generate_stubs.py (vibe coded)
import inspect
import re
from squap import (plot, scatter, errorbar, set_xlim, set_ylim, xlim, ylim, legend, set_title, lock_zoom, subplots, remove_item,
    get_gradient, get_cmap, inf_dline, inf_hline, inf_vline, grid, plot_text, merge_plots, set_interval, on_refresh,
    on_mouse_click, on_mouse_move, get_mouse_pos, on_key_press, add_slider, add_checkbox, add_inputbox, add_button,
    add_dropdown, add_rate_slider, link_boxes, add_input_table, set_active_tab, rename_tab, get_all_boxes, display_fps,
    resize, benchmark, set_input_width, set_input_partition, is_alive, refresh, show_window, show, clear, export,
    export_video, start_recording, get_font, cmap_to_colors)

proxied = [
    plot, scatter, errorbar, set_xlim, set_ylim, xlim, ylim, legend, set_title, lock_zoom, subplots, remove_item,
    get_gradient, get_cmap, inf_dline, inf_hline, inf_vline, grid, plot_text, merge_plots, set_interval, on_refresh,
    on_mouse_click, on_mouse_move, get_mouse_pos, on_key_press, add_slider, add_checkbox, add_inputbox, add_button,
    add_dropdown, add_rate_slider, link_boxes, add_input_table, set_active_tab, rename_tab, get_all_boxes, display_fps,
    resize, benchmark, set_input_width, set_input_partition, is_alive, refresh, show_window, show, clear, export,
    export_video, start_recording, get_font, cmap_to_colors,
]  # your list

all = [
    "widgets",
    "var", "plot", "scatter", "errorbar", "set_xlim", "set_ylim", "xlim", "ylim", "legend", "set_title", "lock_zoom", "subplots",
    "remove_item", "get_gradient", "get_cmap", "inf_dline", "inf_hline", "inf_vline", "grid", "plot_text", "merge_plots", "set_interval",
    "on_refresh", "on_mouse_click", "on_mouse_move", "get_mouse_pos", "on_key_press", "add_slider", "add_checkbox", "add_inputbox", "add_button",
    "add_dropdown", "add_rate_slider", "link_boxes", "add_input_table", "set_active_tab", "rename_tab", "get_all_boxes", "display_fps", "resize", "benchmark", "set_input_width",
    "set_input_partition", "is_alive", "refresh", "show_window", "show", "clear", "export", "export_video", "start_recording", "get_font",
    "ColorType", "ColorsType", "cmap_to_colors"
]

def fix_annotation(annotation: str, package_name: str = "squap") -> str:
    """Replace `pkg.widgets.x.Y` with `widgets.x.Y`"""
    return re.sub(rf'\b{re.escape(package_name)}\.widgets\.', 'widgets.', annotation)

def get_stub_line(method) -> str:
    sig = inspect.signature(method)
    params = [p for name, p in sig.parameters.items() if name != "self"]
    new_sig = sig.replace(parameters=params)
    # inspect.signature renders annotations using their string representation
    sig_str = fix_annotation(str(new_sig))
    return f"def {method.__name__}{sig_str}: ..."


print("from . import widgets")
print("from .helper_funcs import ColorType, ColorsType")
print("from .customisation import Font")
print("from typing import Callable, Iterable, Union, Optional, Any, ForwardRef")
print("import typing")
print("import numpy")
print()
print("import PySide6")
print("import pyqtgraph")
print("from pyqtgraph import mkColor")
print("import matplotlib.colors")

print("\n")
# print("from pyqtgraph")
for method in proxied:
    print(get_stub_line(method))