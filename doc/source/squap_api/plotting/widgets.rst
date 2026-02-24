Widgets And Objects
===================


.. class:: squap.plot_widget.PlotWidget

    All plotting functions are methods of this widget. e.g. :func:`squap.plot` actually redirects to
    :meth:`PlotWidget.plot <squap.plot_widget.PlotWidget.plot>` of the main :class:`PlotWidget <squap.plot_widget.PlotWidget>`. When subplots are created
    with :func:`squap.subplots()`
    you get an ``axs`` list which contains all :class:`PlotWidgets <squap.plot_widget.PlotWidget>`, so that e.g.
    :meth:`axs[0].plot <squap.plot_widget.PlotWidget.plot>` will create a regular plot in the first :class:`PlotWidget <squap.plot_widget.PlotWidget>`.

    .. automethod:: squap.plot_widget.PlotWidget.plot
    .. automethod:: squap.plot_widget.PlotWidget.scatter
    .. automethod:: squap.plot_widget.PlotWidget.errorbar

.. class:: squap.plot_widget.PlotCurve
.. automethod:: squap.plot_widget.PlotCurve.set_data
.. class:: squap.plot_widget.ErrorbarCurve
.. automethod:: squap.plot_widget.ErrorbarCurve.set_data
.. class:: squap.plot_widget.TextCurve
.. automethod:: squap.plot_widget.TextCurve.set_data
.. class:: squap.plot_widget.InfLine
.. automethod:: squap.plot_widget.InfLine.set_data
.. class:: squap.plot_widget.ImageCurve
.. automethod:: squap.plot_widget.ImageCurve.set_data
.. class:: squap.plot_widget.GridCurve
.. automethod:: squap.plot_widget.GridCurve.set_data
