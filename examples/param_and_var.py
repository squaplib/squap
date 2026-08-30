"""
Customisable Plot
=================

Customisable curve displaying all boxes (except color picker box). Also shows :func:`squap.link_boxes`.
"""
import squap
from squap import var
import numpy as np

x = np.linspace(-5, 5, 1000)


def update_func():
    if var.invert_x:
        a = -var.a
    else:
        a = var.a
    y = a*(x-var.c)**var.power+var.b
    if var.autoscale:
        squap.set_xlim(np.min(x), np.max(x))
        squap.set_ylim(np.min(y), np.max(y))
    curve.set_data(x, y)


def reset():
    box5.set_value(0)
    box3.set_value(1.0)
    box8.set_value(1)
    box4.set_value(False)
    box1.set_value(1.0)


def screenshot():
    squap.export(var.filename)


def record():
    var.record_func = squap.start_recording(var.filename, skip_frames=30)
    print("recording started")


def stop_record():
    if var.record_func is not None:
        var.record_func()
    else:
        print("start recording first")


squap.on_refresh(update_func)
box1 = squap.add_rate_slider("c")           # link an absolute and a relative one (see plan)
box2 = squap.add_rate_slider("c", absolute=True)           # link an absolute and a relative one (see plan)
box3 = squap.add_slider("slope", 1, -5, 5, 11, var_name="a", print_value=True)
box4 = squap.add_checkbox("invert_x")
box5 = squap.add_inputbox("b", 0)
box6 = squap.add_button("reset", reset)
box7 = squap.add_checkbox("autoscale")
box8 = squap.add_dropdown("power", options=[1, 2, 3], option_names=["power 1", "power 2", "power 3"])
squap.set_xlim(-5, 5)
squap.set_ylim(-5, 5)
squap.link_boxes([box1, box2])
squap.add_inputbox("filename", "screen_grab")
squap.add_button("screenshot", screenshot)
squap.add_button("start recording", record)
squap.add_button("stop recording", stop_record)
curve = squap.plot()
squap.show()
# pass var_name to add_slider and stuff to make the variable name different from the name in front
