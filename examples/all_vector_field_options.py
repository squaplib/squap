"""
Vector Field Customisation
==========================

Shows all vector field customisation options.
Not thoroughly tested.
"""
import squap
from squap import var
import numpy as np


def update(pos=None):
    if pos is None:
        positions = var.positions
        q_values = var.q_values
    else:
        positions = var.positions + [pos]
        q_values = var.q_values + [var.q]

    centres = np.array(positions)
    # centre = pos
    F[:] = 0

    for index, centre in enumerate(centres):
        x_rel = x_grid - centre[0]
        y_rel = y_grid - centre[1]
        theta = np.arctan2(y_rel, x_rel)
        r = np.sqrt(x_rel**2 + y_rel**2)
        F[:, :, 0] -= q_values[index]*np.cos(theta)/r**var.power
        F[:, :, 1] -= q_values[index]*np.sin(theta)/r**var.power

    curve.set_data(F, border_width=-1, )


def add_atom(pos):
    var.positions.append(pos)
    var.q_values.append(var.q)
    if var.q < 0:
        squap.scatter([pos[0]], [pos[1]], color="red")
    else:
        squap.scatter([pos[0]], [pos[1]], color="blue")


def update_kwargs():
    kwargs = {
        "scale_type": var.scale_type, "head_length": var.head_length, "base_angle": var.base_angle,
        "tail_length": var.tail_length, "tail_width": var.tail_width, "pixel_mode": var.pixel_mode,
        "fill_color": var.fill_color, "border_color": var.border_color, "border_width": var.border_width}
    if var.tip_style == "tip_angle":
        kwargs["tip_angle"] = var.tip_angle
    else:
        kwargs["head_width"] = var.head_width
    curve.set_data(
        **kwargs
        )


def update_dropdown():
    boxes[7].change_params(name=var.tip_style)


def pixel_mode_off():
    boxes[0].set_value(0.005)
    boxes[4].set_value(0.0125)
    boxes[5].set_value(0.0015)
    boxes[6].set_value(False)


def resize_params():
    data = arrow.get_data()
    for box_index, param in zip([9, 10, 5, 7], ["tail_length", "tail_width", "head_length", "head_width"]):
        if var.tip_style == "tip_angle" and param == "head_width":
            continue
        boxes[box_index].set_value(data[param])


min_co, max_co = -0.1, 0.1
var.positions = []
var.q_values = []
Nx, Ny = 15, 20
x = np.linspace(min_co, max_co, Nx)
y = np.linspace(min_co, max_co, Ny)
x_grid, y_grid = np.meshgrid(x, y)

F = np.zeros((Ny, Nx, 2))

squap.on_mouse_move(update)
squap.on_mouse_leave(update)
squap.on_mouse_click(add_atom)

tab1 = squap.add_tab("data")
tab2 = squap.add_tab("vector field properties")

tab1.add_inputbox("q", -1).bind(update)
tab1.add_inputbox("power", 2).bind(update)

boxes = [
    tab2.add_dropdown("scale_type", ["None", "length", "size", "color"], 0),
    tab2.add_inputbox("head_length", 4),
    tab2.add_dropdown("tip_style", ["tip_angle", "head_width"], 0).bind(update_dropdown),
    tab2.add_inputbox("tip_angle", 60),
    tab2.add_inputbox("base_angle", 0),
    tab2.add_inputbox("tail_length", 10),
    tab2.add_inputbox("tail_width", 1.2),
    tab2.add_checkbox("pixel_mode", True),
    tab2.add_color_picker("fill_color", "yellow"),
    tab2.add_color_picker("border_color", "blue"),
    tab2.add_inputbox("border_width", -1),
]
tab2.add_button("change to coordinate mode", pixel_mode_off)

for box in boxes:
    box.bind(update_kwargs)

curve = squap.vector_field(data=F, pos_x=x_grid, pos_y=y_grid)
squap.set_xlim(min_co, max_co)
squap.set_ylim(min_co, max_co)
update((0, 0))
squap.show()
