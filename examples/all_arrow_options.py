"""
Arrow Customisation
===================

Shows all arrow customisation options.
"""
import squap
from squap import var
import numpy as np


var.trigger = 0


def update():
    kwargs = {
        "angle": var.angle, "size": var.size, "position": var.position, "head_length": var.head_length, "base_angle": var.base_angle,
        "tail_length": var.tail_length, "tail_width": var.tail_width, "pixel_mode": var.pixel_mode, "origin": var.origin,
        "fill_color": var.fill_color, "border_color": var.border_color, "border_width": var.border_width, "length": var.length}
    if var.tip_style == "tip_angle":
        pass
        # kwargs["tip_angle"] = var.tip_angle
    else:
        kwargs["head_width"] = var.head_width
    arrow.set_data(
        **kwargs
    )


def update_dropdown():
    boxes[7].change_params(name=var.tip_style)


def pixel_mode_off():
    boxes[5].set_value(0.1)
    boxes[9].set_value(0.25)
    boxes[10].set_value(0.03)
    boxes[11].set_value(False)


def resize_params(flag=False):
    data = arrow.get_data()
    for box_index, param in zip([9, 10, 5, 7], ["tail_length", "tail_width", "head_length", "head_width"]):
        if var.tip_style == "tip_angle" and param == "head_width":
            if flag:
                boxes[box_index].set_value(arrow.get_data()["tip_angle"])
                continue
            else:
                continue

        boxes[box_index].set_value(data[param])


def test_button():
    arrow.setStyle(angle=45)


boxes = [
    squap.add_slider("angle", 0, 0, 360),
    squap.add_inputbox("angle", 0.),
    squap.add_inputbox("size", 1),
    squap.add_inputbox("position", (0., 0.)),
    squap.add_dropdown("origin", ["tip", "center", "tail"]),
    squap.add_inputbox("head_length", 20),
    squap.add_dropdown("tip_style", ["tip_angle", "head_width"], 0).bind(update_dropdown),
    squap.add_inputbox("tip_angle", 60),
    squap.add_inputbox("base_angle", 0),
    squap.add_inputbox("tail_length", 50),
    squap.add_inputbox("tail_width", 6),
    squap.add_checkbox("pixel_mode", True),
    squap.add_color_picker("fill_color", "white"),
    squap.add_color_picker("border_color", "blue"),
    squap.add_inputbox("border_width", -1),
    squap.add_button("test", test_button),
    squap.add_inputbox("length", 1),
]
squap.add_button("change to coordinate mode", pixel_mode_off)

for box in boxes:
    box.bind(update)

boxes[2].bind(resize_params)        # should be called after update
boxes[-1].bind(lambda: resize_params(True))

squap.link_boxes(boxes[0:2])
var.head_width = 10

x = np.linspace(-1, 1, 100)
squap.plot(np.sin(2*np.pi*x), np.cos(2*np.pi*x))
arrow = squap.arrow()
update()
squap.show()
