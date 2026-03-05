# starts off by creating an instance of main_window, containing a plot widget.
from typing import Callable, Iterable       # required for docs

from . import widgets
from .widgets import (MainWindow, FigWidget, TableManager, SubplotWidget, InputTable, Box, PlotCurve, ErrorbarCurve,
                      TextCurve, InfLine, ImageCurve, GridCurve)
from .variables import Variables
from .customisation import get_font, get_gradient, get_cmap, cmap_to_colors
from .helper_funcs import ColorType, ColorsType

import functools        # for copy_docstring decorator
import inspect

from pyqtgraph import setConfigOption
from PySide6.QtCore import QTimer


__all__ = [
    "widgets", "ColorType", "ColorsType",       # things not in __init__.pyi
    "var", "plot", "scatter", "errorbar", "set_xlim", "set_ylim", "xlim", "ylim", "legend", "set_title", "lock_zoom", "subplots",
    "remove_item", "get_gradient", "get_cmap", "inf_dline", "inf_hline", "inf_vline", "grid", "plot_text", "merge_plots", "set_interval",
    "on_refresh", "on_mouse_click", "on_mouse_move", "get_mouse_pos", "on_key_press", "add_slider", "add_checkbox", "add_inputbox", "add_button",
    "add_dropdown", "add_rate_slider", "link_boxes", "add_input_table", "set_active_tab", "rename_tab", "on_tab_change", "get_all_boxes", "display_fps", "resize", "benchmark", "set_input_width",
    "set_input_partition", "is_alive", "refresh", "show_window", "show", "clear", "export", "export_video", "start_recording", "get_font",
    "cmap_to_colors", "enable_autoscale", "disable_autoscale", "enable_autopan", "disable_autopan",
    "make_3D", "scatter_3D", "add_grid_3D", "add_grids_3D", "set_zoom_rate_3D", "set_camera",
    "align_camera"
]

_window = None
_input_table = None
_table_manager = None
_plot_widget_3D = None
var = Variables()


def _copy_docstring(method):
    def decorator(func):
        original_name = func.__name__  # save before update_wrapper overwrites it
        original_module = func.__module__
        sig = inspect.signature(method)
        params = list(sig.parameters.values())
        if params and params[0].name == 'self':
            params = params[1:]
        new_sig = sig.replace(parameters=params)
        functools.update_wrapper(func, method)
        if hasattr(func, '__wrapped__'):
            del func.__wrapped__
        func.__name__ = original_name  # restore
        func.__module__ = original_module
        func.__signature__ = new_sig
        return func
    return decorator


def get_window() -> MainWindow:
    global _window
    if _window is None:
        _window = widgets.MainWindow(var)
    return _window


def get_input_table() -> InputTable:
    global _input_table
    if _input_table is None:
        if get_window().table_manager.first_input_table:     # it is possible to init table widget without this function
            _input_table = get_window().table_manager.first_input_table
        else:
            _input_table = get_window().init_first_tab()
    return _input_table


def get_table_manager():
    """Makes sure that when a function from table_manager is called, the input table is initialised."""
    global _table_manager
    if _table_manager is None:
        get_input_table()
        _table_manager = get_window().table_manager
    return _table_manager


def get_plot_3D():
    """Makes sure that when a function associated to 3D plots, a 3D plot widget gets initialised."""
    global _plot_widget_3D
    if _plot_widget_3D is None:
        _plot_widget_3D = get_window().fig_widget.make_3D()
    return _plot_widget_3D


# <editor-fold desc="wrapped functions">
@_copy_docstring(widgets.SubplotWidget.plot)
def plot(*args, **kwargs):
    return get_window().fig_widget.plot_widget.plot(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.scatter)
def scatter(*args, **kwargs):
    return get_window().fig_widget.plot_widget.scatter(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.errorbar)
def errorbar(*args, **kwargs):
    return get_window().fig_widget.plot_widget.errorbar(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.inf_dline)
def inf_dline(*args, **kwargs):
    return get_window().fig_widget.plot_widget.inf_dline(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.inf_hline)
def inf_hline(*args, **kwargs):
    return get_window().fig_widget.plot_widget.inf_hline(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.inf_vline)
def inf_vline(*args, **kwargs):
    return get_window().fig_widget.plot_widget.inf_vline(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.grid)
def grid(*args, **kwargs):
    return get_window().fig_widget.plot_widget.grid(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.plot_text)
def plot_text(*args, **kwargs):
    return get_window().fig_widget.plot_widget.plot_text(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.imshow)
def imshow(*args, **kwargs):
    return get_window().fig_widget.plot_widget.imshow(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.set_xlim)
def set_xlim(*args, **kwargs):
    return get_window().fig_widget.plot_widget.set_xlim(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.set_ylim)
def set_ylim(*args, **kwargs):
    return get_window().fig_widget.plot_widget.set_ylim(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.xlim)
def xlim(*args, **kwargs):
    return get_window().fig_widget.plot_widget.xlim(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.ylim)
def ylim(*args, **kwargs):
    return get_window().fig_widget.plot_widget.ylim(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.set_xlabel)
def set_xlabel(*args, **kwargs):
    return get_window().fig_widget.plot_widget.set_xlabel(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.set_ylabel)
def set_ylabel(*args, **kwargs):
    return get_window().fig_widget.plot_widget.set_ylabel(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.show_grid)
def show_grid(*args, **kwargs):
    return get_window().fig_widget.plot_widget.show_grid(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.disable_flicker)
def disable_flicker(*args, **kwargs):
    return get_window().fig_widget.plot_widget.disable_flicker(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.enable_autoscale)
def enable_autoscale(*args, **kwargs):
    return get_window().fig_widget.plot_widget.enable_autoscale(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.disable_autoscale)
def disable_autoscale(*args, **kwargs):
    return get_window().fig_widget.plot_widget.disable_autoscale(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.enable_autopan)
def enable_autopan(*args, **kwargs):
    return get_window().fig_widget.plot_widget.enable_autopan(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.disable_autopan)
def disable_autopan(*args, **kwargs):
    return get_window().fig_widget.plot_widget.disable_autopan(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.legend)
def legend(*args, **kwargs):
    return get_window().fig_widget.plot_widget.legend(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.set_title)
def set_title(*args, **kwargs):
    return get_window().fig_widget.plot_widget.set_title(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.lock_zoom)
def lock_zoom(*args, **kwargs):
    return get_window().fig_widget.plot_widget.lock_zoom(*args, **kwargs)

@_copy_docstring(widgets.FigWidget.create_subplots)
def subplots(*args, **kwargs):
    return get_window().fig_widget.create_subplots(*args, **kwargs)

@_copy_docstring(widgets.FigWidget.remove_item)
def remove_item(*args, **kwargs):
    return get_window().fig_widget.remove_item(*args, **kwargs)

@_copy_docstring(widgets.FigWidget.merge_plots)
def merge_plots(*args, **kwargs):
    return get_window().fig_widget.merge_plots(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.set_interval)
def set_interval(*args, **kwargs):
    return get_window().set_interval(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.is_alive)
def is_alive():
    return get_window().is_alive()

@_copy_docstring(widgets.InputTable.add_slider)
def add_slider(*args, **kwargs):
    return get_input_table().add_slider(*args, **kwargs)

@_copy_docstring(widgets.InputTable.add_checkbox)
def add_checkbox(*args, **kwargs):
    return get_input_table().add_checkbox(*args, **kwargs)

@_copy_docstring(widgets.InputTable.add_inputbox)
def add_inputbox(*args, **kwargs):
    return get_input_table().add_inputbox(*args, **kwargs)

@_copy_docstring(widgets.input_widget.InputTable.add_button)
def add_button(*args, **kwargs):
    return get_input_table().add_button(*args, **kwargs)

@_copy_docstring(widgets.InputTable.add_dropdown)
def add_dropdown(*args, **kwargs):
    return get_input_table().add_dropdown(*args, **kwargs)

@_copy_docstring(widgets.InputTable.add_rate_slider)
def add_rate_slider(*args, **kwargs):
    return get_input_table().add_rate_slider(*args, **kwargs)

@_copy_docstring(widgets.InputTable.add_color_picker)
def add_color_picker(*args, **kwargs):
    return get_input_table().add_color_picker(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.on_mouse_click)
def on_mouse_click(*args, **kwargs):
    return get_window().fig_widget.plot_widget.on_mouse_click(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.on_mouse_move)
def on_mouse_move(*args, **kwargs):
    return get_window().fig_widget.plot_widget.on_mouse_move(*args, **kwargs)

@_copy_docstring(widgets.SubplotWidget.get_mouse_pos)
def get_mouse_pos(*args, **kwargs):
    return get_window().fig_widget.plot_widget.get_mouse_pos(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.on_key_press)
def on_key_press(*args, **kwargs):
    return get_window().on_key_press(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.add_table)
def add_input_table(*args, **kwargs):
    return get_window().add_table(*args, **kwargs)

@_copy_docstring(widgets.TableManager.rename_tab)
def rename_tab(*args, **kwargs):
    return get_table_manager().rename_tab(*args, **kwargs)

@_copy_docstring(widgets.TableManager.set_active_tab)
def set_active_tab(*args, **kwargs):
    return get_table_manager().set_active_tab(*args, **kwargs)

@_copy_docstring(widgets.TableManager.get_all_tabs)
def get_all_tabs():
    return get_table_manager().get_all_tabs()

@_copy_docstring(widgets.TableManager.on_tab_change)
def on_tab_change(*args, **kwargs):
    return get_table_manager().on_tab_change(*args, **kwargs)

@_copy_docstring(widgets.TableManager.get_all_boxes)
def get_all_boxes():
    return get_table_manager().get_all_boxes()

@_copy_docstring(widgets.TableManager.get_current_row)
def get_current_row():
    return get_table_manager().get_current_row()

@_copy_docstring(widgets.TableManager.link_boxes)
def link_boxes(*args, **kwargs):
    return get_table_manager().link_boxes(*args, **kwargs)

@_copy_docstring(widgets.TableManager.set_input_partition)
def set_input_partition(*args, **kwargs):
    return get_table_manager().set_input_partition(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.resize_window)
def resize(*args, **kwargs):
    return get_window().resize_window(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.size)
def size():
    return get_window().size()

@_copy_docstring(widgets.MainWindow.set_input_width_ratio)
def set_input_width(*args, **kwargs):
    return get_window().set_input_width_ratio(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.display_fps)
def display_fps(*args, **kwargs):
    return get_window().display_fps(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.benchmark)
def benchmark(*args, **kwargs):
    return get_window().benchmark(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.refresh)
def refresh(*args, **kwargs):
    return get_window().refresh(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.show_window)
def show_window():
    return get_window().show_window()

@_copy_docstring(widgets.MainWindow.on_refresh)
def on_refresh(*args, **kwargs):
    return get_window().on_refresh(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.start)
def show():
    return get_window().start()

def close_window():
    """Closes the window."""
    return get_window().close()

@_copy_docstring(widgets.MainWindow.clear)
def clear():
    return get_window().clear()

@_copy_docstring(widgets.MainWindow.export)
def export(*args, **kwargs):
    return get_window().export(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.export_video)
def export_video(*args, **kwargs):
    return get_window().export_video(*args, **kwargs)

@_copy_docstring(widgets.MainWindow.start_recording)
def start_recording(*args, **kwargs):
    return get_window().start_recording(*args, **kwargs)

@_copy_docstring(widgets.FigWidget.make_3D)
def make_3D(*args, **kwargs):
    return get_window().fig_widget.make_3D(*args, **kwargs)

@_copy_docstring(widgets.plot_widget_3D.SubplotWidget3D.set_zoom_rate)
def set_zoom_rate_3D(*args, **kwargs):
    return get_plot_3D().set_zoom_rate(*args, **kwargs)

@_copy_docstring(widgets.plot_widget_3D.SubplotWidget3D.add_grid)
def add_grid_3D(*args, **kwargs):
    return get_plot_3D().add_grid(*args, **kwargs)

@_copy_docstring(widgets.plot_widget_3D.SubplotWidget3D.add_grids)
def add_grids_3D(*args, **kwargs):
    return get_plot_3D().add_grids(*args, **kwargs)

@_copy_docstring(widgets.plot_widget_3D.SubplotWidget3D.scatter)
def scatter_3D(*args, **kwargs):
    return get_plot_3D().scatter(*args, **kwargs)

@_copy_docstring(widgets.plot_widget_3D.SubplotWidget3D.set_camera)
def set_camera(*args, **kwargs):
    return get_plot_3D().set_camera(*args, **kwargs)

@_copy_docstring(widgets.main_window.MainWindow.align_camera)
def align_camera(*args, **kwargs):
    get_plot_3D()           # make sure 3D plot exists
    get_input_table()       # make sure input tab exists
    return get_window().align_camera(*args, **kwargs)

# </editor-fold>


def enable_numba(enable: bool = True):
    """Enable numba. Can be a little faster, but takes longer to initialize. """
    setConfigOption('useNumba', enable)


def on_next_refresh(func: Callable):          # todo: only works in eventloop, not in show_window style.
    """Calls a function upon next refresh only. """
    QTimer.singleShot(0, func)


# def init_3D():
#     window.init_3D()
#
#
# def add_grid(diagonal):
#     """
#     :param diagonal: A tuple of two points that span the diagonal of a rectangle that lies on or parallel to the
#         xy, yz, or zx plane.
#     :return:
#     """
#     if window.plot_style_3D:
#         window.plot_widget.add_grid(diagonal)
#     else:
#         raise RuntimeError("This function only works in 3D. 3D mode needs to be initialised first. (1003)")
#
#
# def add_grids(size=(0.0, 5.0)):
#     """
#     Adds square grids on the xy, yz and zx planes, spanning from size[0] to size[1].
#
#     :param size: the size of each grid.
#     """
#     if window.plot_style_3D:
#         window.plot_widget.add_grids(size)
#     else:
#         raise RuntimeError("This function only works in 3D. 3D mode needs to be initialised first. (1003)")
#
#
# def align_camera():
#     window.plot_widget.animated = True
#     current_params = window.plot_widget.cameraParams()
#     add_rate_slider("distance", current_params["distance"], changerate=2)
#     row_js_1 = get_current_row()
#     slider_1 = add_slider("azimuth", current_params["azimuth"], 0, 360, n_ticks=72)
#     slider_2 = add_slider("elevation", current_params["elevation"], -90, 90, n_ticks=180)
#     slider_3 = add_slider("fov", current_params["fov"], 0, 180, n_ticks=180)
#     add_rate_slider("x", 0, absolute=True, changerate=5)       # todo: change init_value to current_params.center.x
#     row_js_x = get_current_row()
#     add_rate_slider("y", 0, absolute=True, changerate=5)
#     row_js_y = get_current_row()
#     add_rate_slider("z", 0, absolute=True, changerate=5)
#     row_js_z = get_current_row()
#
#     def update_cam_params():
#         window.plot_widget.setCameraParams(
#             distance=var.distance,
#             azimuth=var.azimuth,
#             elevation=var.elevation,
#             fov=var.fov
#         )
#
#     def rate_slider_update(row):
#         if row == row_js_1:
#             update_cam_params()
#
#     def update_cam_pos():
#         vector = QtGui.QVector3D(
#             var.x,
#             var.y,
#             var.z
#         )
#         window.plot_widget.setCameraPosition(
#             vector
#         )
#
#     def rate_slider_pos_update(row):
#         if row == row_js_x or row == row_js_y or row == row_js_z:
#             update_cam_pos()
#
#     slider_1.valueChanged.connect(update_cam_params)
#     slider_2.valueChanged.connect(update_cam_params)
#     slider_3.valueChanged.connect(update_cam_params)
#     window.input_widget.cellChanged.connect(rate_slider_update)
#     window.input_widget.cellChanged.connect(rate_slider_pos_update)
#     update_cam_params()
#
#     def get_params():
#         print(
#             f"The following function would get you this camera postition: \n"
#             f"squap.set_camera(\n"
#             f"    x={var.x}, y={var.y}, z={var.z}, \n"
#             f"    distance={var.distance}, azimuth={var.azimuth}, "
#             f"elevation={var.elevation}, fov={var.fov}\n)"
#         )
#
#     add_button("print camera parameters", get_params)
#
#

