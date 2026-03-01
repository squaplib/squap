# generate_stubs.py (vibe coded)
import inspect
import re
from squap import (plot, scatter, errorbar, set_xlim, set_ylim, xlim, ylim, legend, set_title, lock_zoom, subplots, remove_item,
    get_gradient, get_cmap, inf_dline, inf_hline, inf_vline, grid, plot_text, merge_plots, set_interval, on_refresh,
    on_mouse_click, on_mouse_move, get_mouse_pos, on_key_press, add_slider, add_checkbox, add_inputbox, add_button,
    add_dropdown, add_rate_slider, link_boxes, add_input_table, set_active_tab, rename_tab, get_all_boxes, display_fps,
    resize, benchmark, set_input_width, set_input_partition, is_alive, refresh, show_window, show, clear, export,
    export_video, start_recording, get_font, cmap_to_colors, make_3D, scatter_3D, add_grid_3D, add_grids_3D,
    set_zoom_rate_3D, set_camera, align_camera)

proxied = [
    plot, scatter, errorbar, set_xlim, set_ylim, xlim, ylim, legend, set_title, lock_zoom, subplots, remove_item,
    get_gradient, get_cmap, inf_dline, inf_hline, inf_vline, grid, plot_text, merge_plots, set_interval, on_refresh,
    on_mouse_click, on_mouse_move, get_mouse_pos, on_key_press, add_slider, add_checkbox, add_inputbox, add_button,
    add_dropdown, add_rate_slider, link_boxes, add_input_table, set_active_tab, rename_tab, get_all_boxes, display_fps,
    resize, benchmark, set_input_width, set_input_partition, is_alive, refresh, show_window, show, clear, export,
    export_video, start_recording, get_font, cmap_to_colors, make_3D, scatter_3D, add_grid_3D, add_grids_3D,
    set_zoom_rate_3D, set_camera, align_camera
]  # all "functions" that are actually methods

all = [
    "widgets",
    "var", "plot", "scatter", "errorbar", "set_xlim", "set_ylim", "xlim", "ylim", "legend", "set_title", "lock_zoom", "subplots",
    "remove_item", "get_gradient", "get_cmap", "inf_dline", "inf_hline", "inf_vline", "grid", "plot_text", "merge_plots", "set_interval",
    "on_refresh", "on_mouse_click", "on_mouse_move", "get_mouse_pos", "on_key_press", "add_slider", "add_checkbox", "add_inputbox", "add_button",
    "add_dropdown", "add_rate_slider", "link_boxes", "add_input_table", "set_active_tab", "rename_tab", "get_all_boxes", "display_fps", "resize", "benchmark", "set_input_width",
    "set_input_partition", "is_alive", "refresh", "show_window", "show", "clear", "export", "export_video", "start_recording", "get_font",
    "ColorType", "ColorsType", "cmap_to_colors"
]


replacements = {"squap.widgets": "widgets", "squap.customisation.Font": "Font", "NoneType": "None"}


def fix_annotation(annotation: str) -> str:
    """Replace `pkg.widgets.x.Y` with `widgets.x.Y`"""
    for old_val, new_val in replacements.items():
        annotation = annotation.replace(old_val, new_val)
    return annotation

def get_stub_line(method) -> str:
    sig = inspect.signature(method)
    params = [p for name, p in sig.parameters.items() if name != "self"]
    new_sig = sig.replace(parameters=params)
    # inspect.signature renders annotations using their string representation
    sig_str = fix_annotation(str(new_sig))
    return f"def {method.__name__}{sig_str}: ..."


print("""
from . import widgets
from .helper_funcs import ColorType, ColorsType
from .customisation import Font
from typing import Callable, Iterable, Union, Optional, Any, ForwardRef
import typing
import numpy

import PySide6
import pyqtgraph
from pyqtgraph import mkColor
import matplotlib.colors

from .variables import Variables
from .helper_funcs import ColorType, ColorsType


var: Variables\n
""")

# print("from pyqtgraph")
for method in proxied:
    print(get_stub_line(method))