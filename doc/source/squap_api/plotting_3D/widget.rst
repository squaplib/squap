Widgets And Objects For 3D Plots
================================

.. currentmodule:: squap.widgets.plot_widget_3D

All functions for creating 3D plots can also be done through a :class:`SubplotWidget3D` object. This is useful for 3D subplots,
or just if you prefer working with widgets and not having to write ``_3D`` after all your functions.
:func:`squap.make_3D` can be used to initialse a :class:`SubplotWidget3D` object, or turn an existing
:class:`plot object <squap.widgets.plot_widget.SubplotWidget>` from :func:`squap.subplots` into a 3D plot.

.. autoclass:: SubplotWidget3D

    .. automethod:: set_camera
    .. automethod:: scatter
    .. automethod:: set_zoom_rate
    .. automethod:: add_grid
    .. automethod:: add_grids
