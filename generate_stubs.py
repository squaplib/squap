# generate_stubs.py (vibe coded)
import inspect
import re
from squap import (plot, scatter, errorbar, set_xlim, set_ylim, xlim, ylim, set_xlabel, set_ylabel, legend, set_title, lock_zoom, subplots, remove_item,
    get_gradient, get_cmap, inf_dline, inf_hline, inf_vline, grid, arrow, vector_field, plot_text, imshow, merge_plots, set_interval, on_refresh,
    on_mouse_click, on_mouse_move, on_mouse_leave, on_mouse_enter, get_mouse_position, mouse_on_screen, mouse_clicked, on_mouse_drag, on_key_press,
    add_slider, add_checkbox, add_inputbox, add_displaybox, add_button, add_dropdown, add_rate_slider, add_joystick, add_color_picker,
    link_boxes, add_tab, set_active_tab, rename_tab, set_table_location, on_tab_change, get_all_boxes, display_fps,
    resize, benchmark, set_input_width, set_input_partition, is_alive, refresh, show_window, show, clear, export,
    export_video, start_recording, get_font, cmap_to_colors, make_3D, scatter_3D, add_grid_3D, add_grids_3D,
    enable_autoscale, disable_autoscale, enable_autopan, disable_autopan, set_zoom_rate_3D, set_camera, get_camera_params, on_camera_change, align_camera, on_var_change)

proxied = [
    plot, scatter, errorbar, set_xlim, set_ylim, xlim, ylim, set_xlabel, set_ylabel, legend, set_title, lock_zoom, subplots, remove_item,
    get_gradient, get_cmap, inf_dline, inf_hline, inf_vline, grid, arrow, vector_field, plot_text, imshow, merge_plots, set_interval, on_refresh,
    on_mouse_click, on_mouse_move, on_mouse_leave, on_mouse_enter, get_mouse_position, mouse_on_screen, mouse_clicked, on_mouse_drag, on_key_press,
    add_slider, add_checkbox, add_inputbox, add_displaybox, add_button, add_dropdown, add_rate_slider, add_joystick, add_color_picker,
    link_boxes, add_tab, set_active_tab, rename_tab, set_table_location, on_tab_change, get_all_boxes, display_fps,
    resize, benchmark, set_input_width, set_input_partition, is_alive, refresh, show_window, show, clear, export,
    export_video, start_recording, get_font, cmap_to_colors, make_3D, scatter_3D, add_grid_3D, add_grids_3D,
    enable_autoscale, disable_autoscale, enable_autopan, disable_autopan, set_zoom_rate_3D, set_camera, get_camera_params, on_camera_change, align_camera, on_var_change
]  # all "functions" that are actually methods

__all__ = [
    "widgets",
    "var", "plot", "scatter", "errorbar", "set_xlim", "set_ylim", "xlim", "ylim", "set_xlabel", "set_ylabel", "legend", "set_title", "lock_zoom", "subplots",
    "remove_item", "get_gradient", "get_cmap", "inf_dline", "inf_hline", "inf_vline", "grid", "arrow", "vector_field", "plot_text", "imshow", "merge_plots", "set_interval",
    "on_refresh", "on_mouse_click", "on_mouse_move", "on_mouse_leave", "on_mouse_enter", "get_mouse_position", "mouse_on_screen", "mouse_clicked", "on_mouse_drag", "on_key_press",
    "add_spacer", "set_spacer", "add_slider", "add_checkbox", "add_inputbox", "add_displaybox", "add_button",
    "add_dropdown", "add_rate_slider", "add_joystick", "link_boxes", "add_tab", "set_active_tab", "rename_tab", "set_table_location", "on_tab_change", "get_all_boxes", "display_fps", "resize", "benchmark", "set_input_width",
    "set_input_partition", "is_alive", "refresh", "show_window", "show", "clear", "export", "export_video", "start_recording", "get_font",
    "cmap_to_colors", "enable_autoscale", "disable_autoscale", "enable_autopan", "disable_autopan",
    "make_3D", "scatter_3D", "plot_3D", "surface_3D", "mesh_3D", "sphere_mesh_3D", "cube_mesh_3D", "cylinder_mesh_3D", "add_grid_3D", "add_grids_3D",
    "set_zoom_rate_3D", "set_camera", "get_camera_params", "on_camera_change", "align_camera", "on_var_change"
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