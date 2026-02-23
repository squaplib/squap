.. _squap.var:

Internal Variables
==================

How To Use Yourself
-------------------

Whenever you make use of a variable that needs to be updated during runtime,
instead of making it a global variable, you can store it in ``squap.var``.
This is a sort of dictionary that is used by the library itself, but is also
incredibly useful for users. For instance, to keep track of the time in the
following snippet. ::

    import squap
    from squap import var
    import numpy as np


    def update():
        curve.set_data(x, np.sin(x+var.t))
        var.t += dt


    var.t = 0
    dt = 0.005
    x = np.linspace(0, 2*np.pi, 50)

    curve = squap.scatter()
    squap.on_refresh(update)
    squap.show()

In this example we store the time in ``squap.var``. The syntax is slightly different
from a dictionary. Instead of ``var["t"]``, we use ``var.t`` to access the variable.

How To Access Internal Information
----------------------------------
The most common use of ``squap.var`` is to access the variables that are controlled
by input boxes. The example below shows how to use this: ::

    import squap
    from squap import var
    import numpy as np


    def update():
        curve.set_data(x, np.sin(x+var.t))


    x = np.linspace(0, 2*np.pi, 50)
    squap.add_slider("t", 0, 0, 2*np.pi)

    curve = squap.scatter()
    squap.on_refresh(update)
    squap.show()

In this example, a slider is initialised, with ``"t"`` as a variable. After this the value
of the slider can be accessed with ``var.t``.

How To Use As Dictionary
------------------------

The variables can also be accessed as a string. This is done as follows: ::

    var_name = "t"
    setattr(var, var_name, 1)

    print("t = ", var.t)
    print("t = ", getattr(var, var_name))

