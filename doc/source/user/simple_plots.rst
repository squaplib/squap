Simple Plots
============

Static Plot
-----------

We start by making a static plot. The syntax is similar to matplotlib: ::

    import squap
    import numpy as np

    x = np.linspace(0, 2*np.pi, 50)
    squap.plot(x, np.sin(x))
    squap.scatter(x, np.cos(x), color="red")

    squap.set_xlim(0, 2*np.pi)
    squap.set_ylim(-1, 1)

    squap.show()

We use :func:`np.linspace <numpy.linspace>` to initialise `x` as `50` evenly spaced points between `0` and :math:`2\pi`.

Time Dependent Plot
-------------------

To make a plot that updates it is useful to make use of the dictionary like object :ref:`squap.var`. Using ``var.t`` we
create a new globally accessible variable which we use to keep track of the time. The following example draws a cosine
with time dependence with a static plot in the background: ::

    import squap
    from squap import var
    import numpy as np


    def update():
        curve.set_data(x, np.cos(x + var.t))
        var.t += dt


    var.t = 0
    dt = 0.005
    x = np.linspace(0, 2*np.pi, 50)
    squap.plot(x, np.sin(x))
    curve = squap.scatter(x, np.cos(x), color="red")

    squap.set_xlim(0, 2 * np.pi)
    squap.set_ylim(-1, 1)
    squap.on_refresh(update)
    squap.show()

First we define an ``update`` function that should run on each refresh, and then we use :func:`squap.on_refresh` to make
sure this function is called on every screen refresh.

Note:
    Try out adding :func:`squap.display_fps()` before `squap.show()` to see how fast the plot is refreshing.

Adding A Slider
---------------

Now we add a slider for the sine function: ::

    import squap
    from squap import var
    import numpy as np


    def update():
        curve_1.set_data(x, np.cos(x + var.t))
        curve_2.set_data(x, np.sin(x + var.a))
        var.t += dt


    var.t = 0
    dt = 0.005
    x = np.linspace(0, 2*np.pi, 50)
    squap.add_slider("a", 0, 0, 2*np.pi)

    curve_1 = squap.scatter(x, np.cos(x), color="red")
    curve_2 = squap.plot(x, np.sin(x))

    squap.set_xlim(0, 2 * np.pi)
    squap.set_ylim(-1, 1)
    squap.on_refresh(update)
    squap.display_fps()
    squap.show()

The slider is added using :func:`squap.add_slider`, where we specify the name is ``a``, the value sarts off at ``0``,
and can be varied between ``0`` and :math:`2\pi`. For other input methods see :ref:`this page <input_boxes>`.



