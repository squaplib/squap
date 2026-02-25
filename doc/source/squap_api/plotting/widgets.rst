Widgets And Objects
===================

.. currentmodule:: squap.widgets.plot_widget

.. autoclass:: PlotWidget

    All plotting functions are methods of this widget. e.g. :func:`squap.plot` actually redirects to
    :py:meth:`PlotWidget.plot <PlotWidget.plot>` of the main :class:`PlotWidget`. When subplots are created
    with :func:`squap.subplots()` you get an ``axs`` list which contains the created :class:`PlotWidgets <PlotWidget>`,
    so that e.g. :meth:`axs[0].plot <PlotWidget.plot>` will create a regular plot in the first :class:`PlotWidget`.

    .. automethod:: squap.widgets.plot_widget.PlotWidget.plot
    .. automethod:: squap.widgets.plot_widget.PlotWidget.scatter
    .. automethod:: squap.widgets.plot_widget.PlotWidget.errorbar

.. autoclass:: PlotCurve

    .. automethod:: set_data

.. autoclass:: ErrorbarCurve

    .. automethod:: set_data

.. autoclass:: TextCurve

    .. automethod:: set_data

.. autoclass:: InfLine

    .. automethod:: set_data

.. autoclass:: ImageCurve

    .. automethod:: set_data

.. autoclass:: GridCurve

    .. automethod:: set_data

