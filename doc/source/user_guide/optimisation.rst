Optimisation
============

This is a short guide on how to speed up slow plots. See :ref:`sphx_glr_auto_examples_optimisation.py` for an example that
illustrates some of these options.

Be Explicit
-----------

Often the simplest speedup can be achieved by explicitly setting :func:`limits <squap.set_xlim>`. Autoscaling is
convenient but slow. Other things you can define explicitly include:

    - Set ``pos`` when using a :class:`QGradient <PySide6.QtGui.QGradient>`.
    - Set ``skip_finite_check`` to ``True`` when using :func:`squap.plot` or similar plotting functions.
    - Set ``Antialiasing`` to ``False`` when using :func:`squap.plot` or similar plotting functions.

Skip Boring Frames
------------------
Sometimes the calculations are simple but require a certain very low timestep. The frames are very similar, so sometimes
you can do multiple timesteps per refresh. todo: include and link to example

Only Update On Button Press
---------------------------
When the plotting is simple, but the calculations are complex, consider only updating when the user presses a button
instead of every time a parameter is changed.
