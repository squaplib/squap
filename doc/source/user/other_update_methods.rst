Other Update Methods
====================

Using :func:`squap.show` with :func:`squap.on_refresh` is not the only way to implement updating plots. Each of the
following has their uses, so before starting a new program decide which method fits best, or combine several.

Using show_window
-----------------
Instead of using :func:`squap.show` with :func:`squap.on_refresh`, it is also possible to use :func:`squap.show_window`
with :func:`squap.refresh()`. This allows you to update the code inside a loop instead of with functions like ``update``
in the previous examples. This method might be a little less robust, so for more complex simulations it is usually better
practice to use :func:`squap.show()`. ::

    import squap
    import numpy as np


    x = np.linspace(0, 2*np.pi, 100)

    curve = squap.scatter(c="r")

    squap.set_xlim(0, 2 * np.pi)
    squap.set_ylim(-1, 1)
    squap.show_window()

    t = 0
    dt = 0.005

    while squap.is_alive():
        curve.set_data(x, np.sin(x+t))
        t += dt
        squap.refresh(call_update_funcs=True)

The loop repeats while :func:`squap.is_alive()` returns ``True``. This makes sure the loop stops when the window is closed.

Using Box.bind
--------------

When there is no time dependence but there are parameters which are controlled by input boxes, it is more useful to
make use of :meth:`Box.bind <squap.widgets.input_widget.Box>`. A function is then bound to a specific box, meaning it
only runs when the value of the box changes. ::

    import squap
    from squap import var
    import numpy as np


    def update():
        curve_1.set_data(var.x, np.cos(var.x + var.b))
        curve_2.set_data(var.x, np.sin(var.x + var.a))


    def update_num_points():
        var.x = np.linspace(0, 2*np.pi, var.N_x)
        update()


    update_boxes = [
        squap.add_slider("a", 0, 0, 2*np.pi),
        squap.add_inputbox("b", 0)
    ]
    for box in update_boxes:
        box.bind(update)

    squap.add_inputbox("N_x", 50, type_func=int).bind(update_num_points)

    curve_1 = squap.scatter(c="r")
    curve_2 = squap.plot()

    update_num_points()

    squap.set_xlim(0, 2 * np.pi)
    squap.set_ylim(-1, 1)
    squap.on_refresh(update)
    squap.show()

Using A Button
--------------

When calculating the next frame is especially slow, consider only updating on the press of a button: ::

    import squap
    from squap import var
    import numpy as np
    import time


    def update():
        time.sleep(1)           # calculate lots of stuff
        curve.set_data(x, np.sin(x + var.a))


    x = np.linspace(0, 2*np.pi, 100)
    squap.add_slider("a", 0, 0, 2*np.pi),
    squap.add_button("update", update)

    curve = squap.scatter(c="r")

    squap.set_xlim(0, 2 * np.pi)
    squap.set_ylim(-1, 1)
    squap.show()

