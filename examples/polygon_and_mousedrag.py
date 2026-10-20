"""
Polygon Plot
============

An example displaying all options for the polygon, and showing off squap.on_mouse_drag.
"""
import squap
from squap import var
import numpy as np


def point_move():
    if not var.pickup is False:         # var.pickup can be zero so if var.pickup fails then.
        pos_arr[:, var.pickup] = squap.get_mouse_position()
        curve_1.set_data(x=pos_arr[0], y=pos_arr[1])
        curve_2.set_data(x=pos_arr[0], y=pos_arr[1])


def point_release():
    var.pickup = False


def mouse_move():
    diffs = np.sqrt(np.sum((pos_arr - np.array(squap.get_mouse_position())[:, np.newaxis])**2, axis=0))
    min_diff = np.min(diffs)
    if min_diff < 0.03:
        if not var.pickup and squap.mouse_clicked():        # makes sure it gets picked up
            var.pickup = np.argmin(diffs)
        hover_point = np.argmin(diffs)
        colors = ["white"]*pos_arr.shape[1]
        colors[hover_point] = "red"
        curve_2.set_data(c=colors)
    else:
        curve_2.set_data(c=["white"]*pos_arr.shape[1])


var.pickup = False
blue = "#0343df"        # xkcd blue
pos_arr = np.array([
    [0, 0, 0.5, 1, 1],
    [0, 1, 1.5, 1, 0]
])

# squap.on_mouse_drag(point_pickup, during_drag=False, on_start=True)
squap.on_mouse_drag(point_move, overwrite_drag=lambda: var.pickup is False)
squap.on_mouse_drag(point_release, during_drag=False, on_finish=True)

squap.on_mouse_move(mouse_move)

curve_1 = squap.polygon(x=pos_arr[0], y=pos_arr[1])
curve_2 = squap.scatter(x=pos_arr[0], y=pos_arr[1], c="white", edge_color=blue, edge_width=2, s=10)

squap.add_color_picker("Fill color", "white", var_name="fill").bind(lambda: curve_1.set_data(fill=var.fill)).trigger()
squap.add_color_picker("Edge color", var_name="edge_color").bind(lambda: curve_1.set_data(edge_color=var.edge_color))
squap.add_inputbox("Edge width", 0, var_name="edge_width").bind(lambda: curve_1.set_data(edge_width=var.edge_width))

squap.set_xlim(-0.3, 1.3)
squap.set_ylim(-0.3, 1.8)

squap.show()
