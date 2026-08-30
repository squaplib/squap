from copy import copy
import numpy as np
from typing import Iterable, Optional

from PySide6.QtGui import QFont, QGradient, QBrush, Qt
from pyqtgraph import (PlotDataItem, PlotWidget, InfiniteLine, TextItem, ImageItem, mkPen, mkBrush, InfLineLabel,
                       GridItem, getConfigOption, ErrorBarItem, ArrowItem)

from ..helper_funcs import is_iter, get_single_color, is_multiple_colors, update_pen, \
    transform_kwargs, ColorType
from ..customisation import cmap_to_gradient, get_cmap, Font


class PlotCurve(PlotDataItem):
    kwarg_mapping = {
        "c": "color", "colour": "color", "w": "width", "downsample_method": "downsampleMethod",
        "skip_finite_check": "skipFiniteCheck", "auto_downsample": "autoDownsample",
        "s": "symbolSize", "size": "symbolSize", "symbol_size": "symbolSize", "pixel_mode": "pxMode",
        "clip_to_view": "clipToView", "symbol_colour": "symbol_color", "symbol_lc": "symbol_line_color",
        "symbol_lw": "symbol_line_width", "gradient": "color", "symbol_edge_color": "symbol_line_color",
        "symbol_edge_width": "symbol_line_width", "sec": "symbol_line_color", "sew": "symbol_line_width",
        "dm": "downsample_method", "sfc": "skipFiniteCheck", "ad": "autoDownsample", "pm": "pxMode",
        "ss": "symbolSize", "ctv": "clipToView", "sc": "symbol_color", "slc": "symbol_line_color",
        "slw": "symbol_line_width", "xerr": "x_err", "yerr": "y_err", "bs": "beam_size", "beamsize": "beam_size",
        "errorbar_colour": "errorbar_color", "ec": "errorbar_color", "ew": "errorbar_width"
    }   # last line is the ones for scatter only, downsample for both, rest for line. (not completely sure)
    all_pen_kwargs = ["line_color", "width", "dashed", "dash_pattern"]
    all_symbol_kwargs = ["symbol_color", "symbol_line_width",  "symbol_line_color", "symbol_size"]
    all_errorbar_kwargs = ["x_err", "y_err", "beam_size", "errorbar_color", "errorbar_width"]

    all_other_kwargs = [
        "symbolSize", "symbolBrush", "symbol", "connect", "pxMode", "antialias", "skipFiniteCheck", "downsample",
        "downsampleMethod", "autoDownsample", "clipToView", "symbolPen"
    ]

    def __init__(self, parent: PlotWidget, curve_type: str = "plot", *args, **kwargs):
        super().__init__()
        self.curve_type = curve_type
        self.parent = parent
        self.errorbar_curve = None

        if curve_type == "plot":
            self.pen = mkPen(color="y")
            self.pen.stored_dash_pattern = None
            self.pen.setCosmetic(True)
            self.setPen(self.pen)
            self.set_data(downsample_method="subsample")                    # defaults are overwritten later
        elif curve_type == "scatter":
            self.pen = None
            self.setPen(self.pen)
            self.set_data(symbol='o', s=6, downsample_method="subsample")   # defaults are overwritten later
            self.setSymbolPen(None)
            self.setSymbolBrush(get_single_color("y"))
        else:
            raise ValueError(f"curve_type {curve_type} is not a valid type of curve.")  # error #1000

        self.symbol_lw = 0
        self.symbol_lc = "white"
        self.gradient = None
        self.errorbar_curve = None

        self.set_data(*args, **kwargs)

    # def setData(self, suppress_warnings=False, *args, **kwargs):
    #     if not suppress_warnings:     # temporarily disabled warning
    #         print("warning")
    #         warnings.warn("Method setData deprecated for usage in squap.")
    #     else:
    #         print("not warning")
        # super(PlotCurve, self).setData(*args, **kwargs)

    # def clear(self):          # clear is already implemented (better than this)
    #     self.setData()

    def set_data(self, x=None, y=None, **kwargs):
        """
        This function updates the data of a :class:`plot <squap.widgets.plot_widget.PlotCurve>`,
        :class:`scatter <squap.widgets.plot_widget.PlotCurve>`, or
        :class:`errorbar <squap.widgets.plot_widget.PlotCurve>`, curve. If both ``x`` and ``y`` are provided, you can set them together
        using ``set_data(x, y, ...)``. If either ``x`` or ``y`` is provided, you can set them individually, for example,
        ``set_data(x=x, ...)`` or ``set_data(y=y, ...)``. Furthermore, you can include additional keyword
        arguments such as ``color`` and ``width`` to customize the appearance of the curve.

        Note:
            For scatter points, ``symbol_color`` is used for the color of points instead of ``color`` when the curve
            was not initialised as a scatter plot.

        Args:
            x: New x-locations of each point. Defaults to the previous value of x.
            y: New y-locations of each point. Defaults to the previous value of y.

        Keyword Args:
            color (:ref:`ColorsType`): Changes the ``color`` of the curve.
                For a scatter-plot this is equivalent to ``symbol_color``, for a
                regular plot it is equivalent to ``line_color``. ``colour`` or ``c`` is also allowed instead of ``color``.
            width (int): Changes the width (in pixels) of the curve. ``w`` is also allowed instead of ``width``.
            line_color (:ref:`ColorType`): Changes the color of the line. See :ref:`ColorsType` for allowed values.
                It can also be a gradient (created with :func:`squap.get_gradient`).
            dashed (bool): If ``True``, draws a dashed line between the points (for more options see ``dash_pattern``).
                Defaults to ``False``.
            dash_pattern (list, optional): How the dashes are spaced. For example, if ``dash_pattern`` is ``[16, 16, 4, 16]``, the pattern
                will be: one dash of 16 pixels long, then a space of 16 pixels long, then a dash of 4 pixels long and then
                a dash of 16 pixels long. This pattern is then repeated. This should be a list with a length that is an
                integer multiple of 2. Setting ``dash_pattern`` will also automatically set ``dashed`` to ``True``. Defaults to ``[16, 16]``.
            line_style(optional, str): todo: some presets for simplicity, ``ls`` is also allowed instead of ``line_style``.
            gradient (:class:`QGradient <PySide6.QtGui.QGradient>`, optional): gradient of the line. Use :func:`squap.get_gradient` to get the gradient. The
                gradient can be seen as a 2D image of a gradient which appears at each pixel that lies on the line.
                When ``style`` of the gradient is set to ``"horizontal"`` or ``"vertical"``, or ``"radial"`` without providing
                ``position``, the bounds of the gradient will be automatically determined when :meth:`set_data <squap.
                plot_widget.PlotCurve.set_data>` is called, which can decrease performance. So, specify ``position`` for
                optimal performance.
            fill_level (float): fills the area under the curve to this Y-value. When provided, either provide ``fill_color``
                or ``fill_gradient``.
            fill_color (:ref:`ColorType`): color of the filled area.
            fill_gradient : gradient of the filled area.
            symbol_color (:ref:`ColorsType`): Changes the color of the symbols. See :ref:`ColorsType` for allowed values.
                If a list of colors is passed, it should be the same length as ``x`` and ``y``.
            symbol_size (int): The size (in pixels) of each symbol. Can also be a list or array.
                `s` and `size` are also allowed instead of `symbol_size`.
            symbol (str): symbol to draw at each (x, y) location. Can be e.g.: ``"o"`` for circles (default), ``"t"`` for
                triangles, ``"s"`` for squares, ``"d"`` for diamonds. For all options see an example that I still have to make.
            symbol_line_width (int): the line width each symbol is drawn with, ``symbol_lw`` and ``slw`` are also allowed.
            symbol_line_color (:ref:`ColorsType`): Change the color of the line around each symbol, see :ref:`ColorsType`
                for allowed values. ``symbol_lc`` and ``slc`` are also allowed.
            pixel_mode (bool): If ``True``, size is specified in pixels. If ``False``, size is specified in data
                coordinates. Defaults to ``True``.
            x_err: Size of the errorbar at each x value. Can be the following types:

                - ``None``: No error in the x-direction.
                - ``float``: x-error at all points.
                - Iterable of same size as ``x``: x-error at each point.
                - Iterable of size `(Nx, 2)`: ``x_err[i, 0]`` is the error on the left at each point, and ``x_err[i, 1]`` is the error on the right at each point ``i``.

                Defaults to ``None``.

            y_err: Same as ``x_err`` but for ``y``.
            beam_size (float): Size of the bars at the ends of the errorbar lines. Default is ``0``.
            errorbar_color (:ref:`ColorType`): Color of the errorbars. Default is ``"y"`` (yellow).
            errorbar_width (int): Width of the errorbar lines. Default is ``1``.
            connect (str or :class:`np.ndarray <numpy.ndarray>`): Can be one of the following options:

                - ``"all"``: Connects all points.
                - ``"pairs"``: Generates lines between every other point.
                - ``"finite"``: Creates a break when a nonfinite points is encountered.
                - ``"auto"``: This will normally use ``"all"``, but if any nonfinite data points are detected,
                  it will automatically switch to ``"finite"``.
                - ``ndarray`` - ``N`` values of ``0`` or ``1``
                  (``N`` being the length of ``x`` and ``y``). Values of ``1`` indicate that the
                  respective point will be connected to the next.

                Defaults to ``"auto"``.
            downsample (int): Reduce the number of samples displayed by the given factor. Default is ``1`` (no downsampling).
            downsample_method (str): Can be one of the following options:

                - ``"subsample"``: Downsample by taking the first of ``downsample`` samples. This method is fastest and least accurate.
                  Length of datasets will be divided by downsample
                - ``"mean"``: Downsample by taking the mean of ``downsample`` samples. Length of datasets will be divided by ``downsample``.
                - ``"peak"``: Downsample by drawing a saw wave that follows the min and max of the original data. This
                  method produces the best visual representation of the data but is slower. Length of dataset will
                  stay the same.

                Defaults to ``"mean"``.
            auto_downsample (bool): Can increase performance by not drawing one pixel multiple times, but is slower
                for less data. Defaults to ``False``.
            antialias (bool): Antialiasing can be disabled for a minor performance increase. Default is ``True``.
            skip_finite_check (bool): Optimization flag that can speed up plotting by not checking and compensating
                for ``NaN`` values. If set to ``True``, and ``NaN`` values exist, unpredictable behavior will occur. The data may
                not be displayed or the plot may take a significant performance hit. Defaults to ``False``.
            clip_to_view (bool): If True, only data visible within the X range of the containing ViewBox is plotted.
                This can improve performance when plotting very large data sets where only a fraction of the data
                is visible at any time.
        """
        if x is None and y is None:     # needed for autoscaling gradient, so done here.
            x, y = self.getData()
            xy_changed = False
        else:
            if y is None:
                y = self.getData()[1]
                if y is None:
                    y = np.zeros(len(x))
            if x is None:
                x = self.getData()[0]
                if x is None:
                    x = np.zeros(len(y))
            xy_changed = True

        other_kwargs = {}           # `setData` needs to be done in one command, so other kwargs that need to be passed
        # to it are added to this dict. If the data is updated, this is also passed as the kwargs.
        if kwargs:      # if anything else is changed, run this bit
            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)

            if "color" in new_kwargs:
                if self.curve_type == "scatter":
                    new_kwargs["symbol_color"] = new_kwargs["color"]
                else:
                    new_kwargs["line_color"] = new_kwargs["color"]

                # changes color if color of the line is changed using the color kwarg.
                if self.errorbar_curve is not None and "errorbar_color" not in new_kwargs:
                    new_kwargs["errorbar_color"] = new_kwargs["color"]

            errorbar_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_errorbar_kwargs if kwarg in new_kwargs}
            if errorbar_kwargs:         # self.errorbar_curve needs to be set before "color" is handled
                if self.errorbar_curve is None:
                    self.errorbar_curve = ErrorbarCurve(self)
                    self.parent.addItem(self.errorbar_curve)
                    self.parent.curves.append(self.errorbar_curve)
                    if "errorbar_color" not in new_kwargs:
                        errorbar_kwargs["color"] = self.pen.color()

                self.errorbar_curve.set_data(x=x, y=y, **errorbar_kwargs)
            elif self.errorbar_curve is not None and xy_changed:
                self.errorbar_curve.set_data(x=x, y=y)

            pen_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_pen_kwargs if kwarg in new_kwargs}
            if pen_kwargs:
                if "line_color" in pen_kwargs:
                    if isinstance(pen_kwargs["line_color"], QGradient):
                        self.gradient = pen_kwargs["line_color"]
                        if self.gradient.autoscale:
                            if self.gradient.style == "horizontal":
                                self.gradient.setStart(min(x), 0)
                                self.gradient.setFinalStop(max(x), 0)
                            elif self.gradient.style == "vertical":
                                self.gradient.setStart(0, min(y))
                                self.gradient.setFinalStop(0, max(y))
                            else:           # gradient.style must be "radial" here
                                self.gradient.setStart(min(x), min(y))

                        cmap_to_gradient(self.gradient.cmap, self.gradient)
                    pen_kwargs["color"] = pen_kwargs["line_color"]      # handled by update_pen
                if self.pen is None:
                    self.pen = mkPen()
                    self.pen.stored_dash_pattern = None

                if update_pen(self.pen, **pen_kwargs) is not None:
                    self.setPen(self.pen)
                else:
                    self.setPen(None)
            symbol_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_symbol_kwargs if kwarg in new_kwargs}
            if symbol_kwargs:
                if "symbol_color" in symbol_kwargs:
                    col = symbol_kwargs["symbol_color"]
                    if is_multiple_colors(col):
                        new_kwargs["symbolBrush"] = [get_single_color(col_i) for col_i in col]
                    else:
                        new_kwargs["symbolBrush"] = get_single_color(col)

                if "symbol_line_width" in symbol_kwargs or "symbol_line_color" in symbol_kwargs:
                    if "symbol_line_width" in symbol_kwargs:
                        self.symbol_lw = symbol_kwargs["symbol_line_width"]
                    if "symbol_line_color" in symbol_kwargs:
                        self.symbol_lc = symbol_kwargs["symbol_line_color"]
                    mult_col, mult_lw = is_multiple_colors(self.symbol_lc), is_iter(self.symbol_lw)
                    if mult_col:
                        if mult_lw:
                            symbol_pen = [
                                mkPen(get_single_color(color), width=width) for color, width in zip(self.symbol_lc, self.symbol_lw)
                            ]
                        else:
                            symbol_pen = [mkPen(get_single_color(color), width=self.symbol_lw) for color in self.symbol_lc]
                    else:
                        if mult_lw:
                            symbol_pen = [mkPen(get_single_color(self.symbol_lc), width=width) for width in self.symbol_lw]
                        else:
                            symbol_pen = mkPen(get_single_color(self.symbol_lc), width=self.symbol_lw)
                    new_kwargs["symbolPen"] = symbol_pen

            other_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_other_kwargs if kwarg in new_kwargs}
            if "symbolSize" in other_kwargs:
                if other_kwargs["symbolSize"] <= 0:
                    other_kwargs["symbol"] = None

        x_is_iter_or_none, y_is_iter_or_none = is_iter(x) or x is None, is_iter(y) or y is None
        if x_is_iter_or_none == y_is_iter_or_none:  # Ensures both are iterables or neither
            self.setData(x=[x] if not x_is_iter_or_none else x,
                         y=[y] if not y_is_iter_or_none else y,
                         **other_kwargs)
        else:
            raise TypeError(f"`x` and `y` must both be iterables or both not be iterables. "
                            f"Currently, `x` is {'not ' if not is_iter(x) else ''}iterable "
                            f"and `y` is {'not ' if not is_iter(y) else ''}iterable.")

    def clear(self):    # normal clear doesn't do much
        self.set_data(x=[], y=[])


class ErrorbarCurve(ErrorBarItem):
    """Is added to PlotCurve as attribute when an errorbar curve is initialised. Users probably will not interact with this object."""
    kwarg_mapping = {"xe": "x_err", "xerr": "x_err", "yerr": "y_err", "beamsize": "beam_size",
                     "bs": "beam_size", "c": "color", "colour": "color", "w": "width", "errorbar_color": "color",
                     "errorbar_width": "width"}

    def __init__(self, parent, x_err: None | float | Iterable = None, y_err: None | float | Iterable = None,
                 beam_size: float = 0.0, color: ColorType = "white", width: int = 1):
        super().__init__()
        self.parent = parent        # for giving just one value for x_err or y_err
        self.pen = None
        self.old_x_err = None
        self.old_y_err = None
        self.set_data(x_err=x_err, y_err=y_err, beam_size=beam_size, color=color, width=width)

    def set_data(self, *args, **kwargs):
        """Used internally when plotting with an errorbar. Users will only interact with the :class:`~squap.widgets.plot_widget.PlotCurve`."""
        if args:
            if len(args) == 1:
                kwargs["y"] = args[0]
            elif len(args) == 2:
                kwargs["x"] = args[0]
                kwargs["y"] = args[1]
            else:
                raise ValueError(f"Too many args provided. Can be 2 maximum, but is now {len(args)}.")

        if kwargs:
            if "x_err" in kwargs or "y_err" in kwargs:
                if "x_err" not in kwargs:
                    if self.old_x_err is None:
                        kwargs["x_err"] = 0
                    kwargs["x_err"] = self.old_x_err
                else:
                    x_err = kwargs["x_err"]
                    self.old_x_err = x_err
                if "y_err" not in kwargs:
                    if self.old_y_err is None:
                        kwargs["y_err"] = 0
                    kwargs["y_err"] = self.old_y_err
                else:
                    y_err = kwargs["y_err"]
                    self.old_y_err = y_err

            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
            errorbar_kwargs = {}

            # repeat the same thing for x and y
            if "x_err" in kwargs or "y_err" in kwargs:
                for arg_strings in [["x_err", "left", "right"], ["y_err", "bottom", "top"]]:
                    kwarg_name = arg_strings[0]
                    errorbar_kwarg1 = arg_strings[1]
                    errorbar_kwarg2 = arg_strings[2]

                    # is a little vague right now, fill in arg_strings for x to get clearer code.
                    if kwarg_name in new_kwargs:
                        if isinstance(new_kwargs[kwarg_name], int) or isinstance(new_kwargs[kwarg_name], float):
                            num_points = len(self.parent.xData)
                            errorbar_kwargs[errorbar_kwarg1] = np.full(num_points, new_kwargs[kwarg_name])
                            errorbar_kwargs[errorbar_kwarg2] = np.full(num_points, new_kwargs[kwarg_name])
                        elif isinstance(new_kwargs[kwarg_name], Iterable):
                            kwarg_shape = np.shape(new_kwargs[kwarg_name])
                            if len(kwarg_shape) == 1 or kwarg_shape[1] == 1:       # if it has only one dimension
                                errorbar_kwargs[errorbar_kwarg1] = new_kwargs[kwarg_name]
                                errorbar_kwargs[errorbar_kwarg2] = new_kwargs[kwarg_name]
                            elif kwarg_shape[1] == 2:
                                errorbar_kwargs[errorbar_kwarg1] = new_kwargs[kwarg_name][0]
                                errorbar_kwargs[errorbar_kwarg2] = new_kwargs[kwarg_name][1]

            if "beam_size" in new_kwargs:
                errorbar_kwargs["beam"] = new_kwargs["beam_size"]
            if "x" in new_kwargs:
                errorbar_kwargs["x"] = new_kwargs["x"]
            if "y" in new_kwargs:
                errorbar_kwargs["y"] = new_kwargs["y"]

            pen_kwargs = {}
            if "color" in new_kwargs:
                pen_kwargs["color"] = new_kwargs["color"]
            if "width" in new_kwargs:
                pen_kwargs["width"] = new_kwargs["width"]
            if pen_kwargs != {}:
                if self.pen is None:
                    self.pen = mkPen()
                update_pen(self.pen, **pen_kwargs)
                errorbar_kwargs["pen"] = self.pen

            self.setData(**errorbar_kwargs)

    def clear(self):    # normal clear doesn't do much
        self.set_data(x=[], y=[], x_err=[], y_err=[])


class TextCurve(TextItem):
    kwarg_mapping = {
        "c": "color", "colour": "color", "text_color": "color", "fill": "fill_color", "fc": "fill_color",
        "tw": "text_width"
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.set_data(*args, **kwargs)

    def set_data(self, *args, **kwargs):
        """Updates an existing text object. Takes the same arguments and keyword arguments as :func:`squap.plot_text`."""
        if args:
            self.setText(str(args[0]))
            if is_iter(args[1]):
                self.setPos(*args[1])
            elif len(args) > 2:
                self.setPos(args[1], args[2])

        if kwargs:
            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
            if "text" in new_kwargs:
                self.setText(new_kwargs["text"])
            if "color" in new_kwargs:
                self.setColor(get_single_color(new_kwargs["color"]))
            if "angle" in new_kwargs:
                self.setAngle(new_kwargs["angle"])
            if "font" in new_kwargs:
                self.setFont(new_kwargs["font"])
            if "html" in new_kwargs:
                self.setHtml(new_kwargs["html"])
            if "text_width" in new_kwargs:
                self.setTextWidth(new_kwargs["text_width"])
            if "fill_color" in new_kwargs:
                # if isinstance(new_kwargs["fill_color"], QGradient):
                #     gradient = new_kwargs["fill_color"]
                #     cmap_to_gradient(gradient.cmap, gradient)
                self.fill = QBrush(get_single_color(new_kwargs["fill_color"]))
            border_pen_kwargs = {}
            if "border_color" in new_kwargs:
                border_pen_kwargs["color"] = new_kwargs["border_color"]
            if "border_width" in new_kwargs:
                border_pen_kwargs["width"] = new_kwargs["border_width"]
            if border_pen_kwargs:
                if self.border.style() == Qt.PenStyle.NoPen:     # self.border is automatically the pen that is used to draw the border
                    self.border = mkPen(**border_pen_kwargs)
                else:
                    update_pen(self.border, **border_pen_kwargs)
                    self.getViewBox().update()
                    # is not properly updated when only width changes so needs to done manually

    def set_font(self, *args, **kwargs):
        if "font" in kwargs:
            font = kwargs["font"]
            if isinstance(font, QFont):
                self.setFont(font)
                return
        if args:
            if isinstance(args[0], QFont):
                self.setFont(args[0])
                return

        self.setFont(Font(*args, **kwargs))

    def font(self):
        return self.textItem.font()


class InfLine(InfiniteLine):
    kwarg_mapping = {
        "c": "color", "colour": "color", "w": "width", "ls": "line_style", "hc": "hover_color",
        "hw": "hover_width", "gradient": "color"
    }
    all_pen_kwargs = ["color", "width", "dashed", "dash_pattern", "line_style"]
    all_label_kwargs = ["label", "label_text", "movable", "label_movable", "label_position", "label_anchors"]

    def __init__(self, pos, angle, bounds=None, **kwargs):
        super().__init__(pos=pos, angle=angle, bounds=bounds)
        self.pen = mkPen(color="y")
        self.pen.stored_dash_pattern = None
        self.hover_color = None
        self.hover_width = None
        self.movable = False
        self.label_movable = None
        self.label_text = "{value}"
        self.label_position = 0.5
        self.label_anchors = None
        self.line_movable = None
        self.label = None
        self.set_data(**kwargs)

    def set_data(self, pos: Optional[float | Iterable[float]]=None, **kwargs):
        """Updates an existing line object. Takes the same arguments and keyword arguments as :func:`squap.inf_dline`."""
        if pos is not None:
            self.setValue(pos)

        if kwargs:
            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)

            if "angle" in new_kwargs:
                self.setAngle(new_kwargs["angle"])
                vb = self.getViewBox()
                vb._matrixNeedsUpdate = True
                vb.update()
            if "bounds" in new_kwargs:
                self.setBounds(new_kwargs["bounds"])
            if "span" in new_kwargs:
                self.setSpan(*new_kwargs["span"])
                vb = self.getViewBox()
                if vb:
                    vb._matrixNeedsUpdate = True
                    vb.update()
            if "name" in new_kwargs:
                self.setName(new_kwargs["name"])
            if "movable" in new_kwargs or "line_movable" in new_kwargs:
                self.setMovable(self.movable if self.line_movable is None else self.line_movable)

            for attr in ["movable", "label_movable", "label_text", "label_position", "label_anchors", "line_movable",
                         "hover_color", "hover_width", "label"]:
                if attr in new_kwargs:  # updates all self.attr
                    setattr(self, attr, new_kwargs[attr])

            pen_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_pen_kwargs if kwarg in new_kwargs}
            if pen_kwargs:
                if "color" in pen_kwargs:
                    if isinstance(pen_kwargs["color"], QGradient):
                        gradient = pen_kwargs["color"]
                        if gradient.autoscale:     # todo: autoscale to min and max when span is given or when bounds is given
                            raise ValueError("`gradient` can not autoscale for infinite lines. Provide `position` to "
                                             "`get_gradient`")
                        cmap_to_gradient(gradient.cmap, gradient)
                    pen_kwargs["color"] = pen_kwargs["color"]      # handled by update_pen
                update_pen(self.pen, **pen_kwargs)
                self.setPen(self.pen)

            hover_pen_kwargs = {}
            if (self.line_movable is None and self.movable) or self.line_movable == True:
                if self.hover_color is not None:
                    hover_pen_kwargs["color"] = self.hover_color
                if self.hover_width is not None:
                    hover_pen_kwargs["width"] = self.hover_width
            if hover_pen_kwargs or pen_kwargs:
                hover_pen = copy(self.pen)          # makes sure eg. dashing is consistent with normal line
                update_pen(hover_pen, **hover_pen_kwargs)
                self.setHoverPen(hover_pen)

            label_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_label_kwargs if kwarg in new_kwargs}
            if label_kwargs and self.label:
                if isinstance(self.label, InfLineLabel):
                    if "movable" in new_kwargs or "label_movable" in new_kwargs:
                        self.label.setMovable(self.movable if self.label_movable is None else self.label_movable)
                    if "label_position" in label_kwargs:
                        self.label.setPosition(new_kwargs["position"])
                    if "label_text" in label_kwargs:
                        self.label.setFormat(new_kwargs["text"])
                    if "label_anchors" in label_kwargs:
                        if label_kwargs["label_anchors"]:
                            self.label.anchors = label_kwargs["label_anchors"]
                else:
                    self.label = InfLineLabel(
                        self, self.label_text,
                        self.movable if self.label_movable is None else self.label_movable,
                        self.label_position, self.label_anchors
                    )


class ImageCurve(ImageItem):
    kwarg_mapping = {
        "loc": "location", "z": "data", "image": "data", "bc": "border_color", "border": "border_color"
    }

    def __init__(self, data=None, **kwargs):        # **kwargs for aliases
        super().__init__(axisOrder="row-major")
        self.auto_levels = None         # will be updated before first usage, initial value is irrelevant.
        self.rect = None
        self.data_shape = data.shape if data is not None else None
        self.data = data            # Needs to be stored for when cmap is given and data is not changed.
        self.cmap = None            # Needs to be stored for when data is given and cmap is not changed

        self.set_data(**kwargs)

    def set_data(self, data=None, **kwargs):
        """Updates an existing image object. Takes the same arguments and keyword arguments as :func:`squap.imshow`."""
        kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
        final_kwargs = {}
        if data is not None:
            if self.cmap is not None:
                final_kwargs["image"] = self.cmap(data)/255
            else:
                final_kwargs["image"] = data

            if data.shape != self.data_shape:
                self.data_shape = data.shape if data is not None else None
                if "location" not in kwargs:
                    final_kwargs["rect"] = self.rect
            self.data = data
            # test_print(final_kwargs["image"])

        if "location" in kwargs:
            if kwargs["location"] is None:
                final_kwargs["rect"] = (0, 0, 1, 1)
            else:
                if len(kwargs["location"]) != 4:
                    raise TypeError(f"`location` must be a length 4-iterable")
                else:
                    loc = kwargs["location"]
                    final_kwargs["rect"] = (loc[0], loc[1], loc[2]-loc[0], loc[3]-loc[1])
            self.rect = final_kwargs["rect"]
        if "cmap" in kwargs:
            cmap = get_cmap(kwargs["cmap"])
            self.cmap = cmap
            if data is not None:
                final_kwargs["image"] = cmap(data)/255      # image want values between 0 and 1
            # print(cmap(data).shape)

        if "auto_levels" in kwargs:
            self.auto_levels = kwargs["auto_levels"]    # updates self.auto_levels to most recent value
            final_kwargs["autoLevels"] = self.auto_levels
        # if "levels" in kwargs:
        #     final_kwargs["levels"] = kwargs["levels"]
        if not self.auto_levels:
            if self.data_shape is not None:
                final_kwargs["levels"] = [0, 1]

        if "axis_order" in kwargs:
            final_kwargs["axisOrder"] = kwargs["axis_order"]
            self.setOpts(kwargs["axis_order"])
        if "border_color" in kwargs:
            final_kwargs["border"] = kwargs["border_color"]

        self.setImage(**final_kwargs)


class GridCurve(GridItem):
    kwarg_mapping = {
        "grid_spacing": "tick_spacing", "gs": "tick_spacing", "spacing": "tick_spacing", "ts": "tick_spacing",
        "c": "color", "colour": "color", "w": "width"
    }
    all_pen_kwargs = ["color", "width"]

    def __init__(self, **kwargs):
        super().__init__()
        self.pen = mkPen(getConfigOption('foreground'))
        self.setTextPen(None)
        self.set_data(**kwargs)

    def set_data(self, **kwargs):
        """Updates an existing grid object. Takes the same arguments and keyword arguments as :func:`squap.grid`."""
        kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
        if "tick_spacing" in kwargs:
            tick_spacing = kwargs["tick_spacing"]
            if is_iter(tick_spacing):
                if len(tick_spacing) != 2:
                    raise TypeError(f"`tick_spacing` must be a length 2-iterable, or a single value")
                if is_iter(tick_spacing[0]):
                    self.setTickSpacing(*tick_spacing)
                else:
                    self.setTickSpacing([tick_spacing[0]], [tick_spacing[1]])
            else:
                self.setTickSpacing([tick_spacing, tick_spacing])

        pen_kwargs = {kwarg: kwargs[kwarg] for kwarg in self.all_pen_kwargs if kwarg in kwargs}
        if pen_kwargs:
            if "color" in pen_kwargs:
                if isinstance(pen_kwargs["color"], QGradient):
                    gradient = pen_kwargs["color"]
                    if gradient.autoscale:  # todo: autoscale to min and max when span is given or when bounds is given
                        raise ValueError("`gradient` can not autoscale for grids. Provide `position` to "
                                         "`get_gradient`")
                    cmap_to_gradient(gradient.cmap, gradient)
                pen_kwargs["color"] = pen_kwargs["color"]  # handled by update_pen
            update_pen(self.pen, **pen_kwargs)
            self.setPen(self.pen)


class ArrowCurve(ArrowItem):
    kwarg_mapping = {
        "c": "fill_color", "colour": "fill_color", "color": "fill_color", "fc": "fill_color",
        "fill_colour": "fill_color", "bc": "border_color",
        "border_colour": "border_color", "bw": "border_width",
        "hl": "head_length", "hw": "head_width", "pm": "pixel_mode", "ta": "tip_angle", "ba": "base_angle",
        "tl": "tail_length", "tw": "tail_width",
        "pos": "position", "location": "position", "loc": "position",
    }
    final_kwarg_mapping = {
        "angle": "angle", "head_length": "headLen", "head_width": "headWidth", "pixel_mode": "pxMode",
        "tip_angle": "tipAngle", "base_angle": "baseAngle", "tail_length": "tailLen", "tail_width": "tailWidth",
    }

    def __init__(self, view_box, **kwargs):
        super().__init__()
        self.view_box = view_box        # required for different origin when pixel_mode is `True`

        self.border_pen = mkPen(color="b", width=-1)
        self.brush = mkBrush(color="white")

        self.pixel_mode = None
        self.angle = None
        self.origin = "tip"
        self.head_length = 0
        self.head_width = 0
        self.tail_length = 0
        self.tail_width = 0
        self.tip_angle = 0
        self.position = (0, 0)
        self.size = 1
        self.length = 1
        self.tip_type = "angle"     # either "angle" or "width"

        kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
        self.set_data(**kwargs)

    def set_data(self, **kwargs):
        """Updates an existing arrow object. Takes the same arguments and keyword arguments as :func:`squap.arrow`."""
        # since some variation of the arguments are all accepted by setStyle, I will work with the pyqtgraph names in
        # this function.
        kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
        final_kwargs = {value: kwargs[key] for key, value in self.final_kwarg_mapping.items() if key in kwargs}
        if "color" in kwargs:
            kwargs["fill_color"] = kwargs["color"]
            kwargs["border_color"] = kwargs["color"]

        if "fill_color" in kwargs:
            final_kwargs["brush"] = QBrush(get_single_color(kwargs["fill_color"]))
        border_pen_kwargs = {}
        if "border_color" in kwargs:
            border_pen_kwargs["color"] = kwargs["border_color"]
        if "border_width" in kwargs:
            border_pen_kwargs["width"] = kwargs["border_width"]
        if border_pen_kwargs:
            update_pen(self.border_pen, **border_pen_kwargs)
            self.setPen(self.border_pen)  # Changing it via setStyle doesn't trigger a redraw.

        self.head_width = self.get_data()["head_width"]

        if "origin" in kwargs:
            self.origin = kwargs["origin"]

        if "tail_length" in kwargs:
            self.tail_length = kwargs["tail_length"]
        if "tail_width" in kwargs:
            self.tail_width = kwargs["tail_width"]
        if "head_length" in kwargs:
            self.head_length = kwargs["head_length"]

        if "tip_angle" in kwargs:
            self.tip_angle = kwargs["tip_angle"]
            self.tip_type = "angle"

        if "position" in kwargs:
            self.position = np.array(kwargs["position"])

        if "pixel_mode" in kwargs:
            self.pixel_mode = kwargs["pixel_mode"]
            if "angle" not in kwargs and self.pixel_mode:
                final_kwargs["angle"] = -self.angle

        if "angle" in kwargs:
            self.angle = kwargs["angle"]
            if self.pixel_mode:
                final_kwargs["angle"] = -self.angle

        if kwargs:      # The code below should be run very often upon parameter change, so it is just always done.
            if self.origin == "tip":
                position = self.position
            else:
                length = self.head_length + self.tail_length
                rad_angle = self.angle / 360 * 2 * np.pi
                dpos = length * np.array([np.cos(rad_angle), np.sin(rad_angle)])

                if self.pixel_mode:         # dpos is in pixels; convert to scene units
                    view = self.view_box
                    if view is not None:
                        pixel_size = view.viewPixelSize()
                        dpos = dpos * np.array(pixel_size)

                if self.origin == "tail":
                    position = self.position - dpos
                elif self.origin == "center":
                    position = self.position - dpos/2
                else:
                    raise ValueError(f"Origin must be either 'tip', 'tail' or 'center', is now '{self.origin}'.")

            self.setPos(*position)

        if "size" in kwargs:
            resize_factor = kwargs["size"] / self.size
            self.size = kwargs["size"]
            for prop in ["tail_length", "tail_width", "head_length", "head_width"]:
                if prop == "head_width" and self.tip_type == "angle":
                    continue

                new_value = self.__getattribute__(prop)*resize_factor
                self.__setattr__(prop, new_value)
                final_kwargs[self.final_kwarg_mapping[prop]] = new_value

        if "length" in kwargs:
            resize_factor = kwargs["length"] / self.length
            self.length = kwargs["length"]
            if self.tip_type == "angle":        # If tip_type is "angle" make sure the head_width stays the same
                self.head_width = self.get_data()["head_width"]
                final_kwargs["headWidth"] = self.head_width
                self.tip_type = "width"
            for prop in ["tail_length", "head_length"]:
                new_value = self.__getattribute__(prop)*resize_factor
                self.__setattr__(prop, new_value)
                final_kwargs[self.final_kwarg_mapping[prop]] = new_value

        self.setStyle(**final_kwargs)
        self.setPen(self.border_pen)        # Setting the style often resets the Pen to default, not sure when
        # this happens, so I just always reset the pen.

    def get_data(self):
        if self.tip_type == "angle":
            self.head_width = self.head_length * np.tan(np.radians(self.tip_angle * 0.5))
        else:
            self.tip_angle = 2 * np.degrees(np.arctan(self.head_width / self.head_length))
        return {
            "border_pen": self.border_pen, "brush": self.brush, "pixel_mode": self.pixel_mode,
            "angle": self.angle, "origin": self.origin, "head_length": self.head_length,
            "head_width": self.head_width, "tail_length": self.tail_length, "tail_width": self.tail_width,
            "tip_angle": self.tip_angle, "position": self.position, "size": self.size, "tip_type": self.tip_type}


class VectorFieldCurve:
    kwarg_mapping = {
        "c": "fill_color", "colour": "fill_color", "color": "fill_color", "fc": "fill_color",
        "fill_colour": "fill_color", "bc": "border_color",
        "border_colour": "border_color", "bw": "border_width",
        "hl": "head_length", "hw": "head_width", "pm": "pixel_mode", "ta": "tip_angle", "ba": "base_angle",
        "tl": "tail_length", "tw": "tail_width",
        "pos": "position", "location": "position", "loc": "position",
    }
    arrow_kwargs = [
        "size", "head_length", "head_width", "pixel_mode", "tip_angle", "base_angle", "tail_length", "tail_width"]

    def __init__(self, parent, data: np.ndarray, **kwargs):
        self.parent = parent        # adds arrows via parent

        self.scale_type = None
        self.absolute = False
        self.cmap = None
        self.current_arrow_kwargs = {}
        self.arrows = []
        self.shape = (0, 0, 0)
        self.pos_arr = np.zeros((0, 0, 2))
        self.data = np.zeros((0, 0, 2))

        self.set_data(data, **kwargs)

    def set_data(self, data: Optional[np.ndarray] = None, **kwargs):
        """Updates an existing vector field object. Takes the same arguments and keyword arguments as
        :func:`squap.vector_field`."""
        # The following handles pos_x and pos_y. If one of them is passed, just that one is changed. If one of them is
        # passed and the shape is different from what it was, the other becomes linspace between 0 and 1 of the same
        # shape. If both are passed, and the shapes mismatch, an error is thrown. If both are passed correctly
        # self.pos_arr is constructed properly.
        if "pos_x" in kwargs or "pos_y" in kwargs:
            if "pos_x" in kwargs:
                pos_x = kwargs["pos_x"]
                if pos_x.shape != self.pos_arr.shape[:2]:  # if the shape is new
                    self.pos_arr = np.zeros((*pos_x.shape, 2))
                    if "pos_y" in kwargs:
                        if kwargs["pos_y"].shape != pos_x.shape[:2]:
                            raise ValueError(f"`pos_x` and `pos_y` should be the same shape. They are now shapes "
                                             f"{pos_x.shape} and {kwargs['pos_y'].shape}, respectively.")
                        else:
                            self.pos_arr[:, :, 1] = kwargs["pos_y"]
                    else:
                        pos_y = np.linspace(0, 1, pos_x.shape[0])[:, np.newaxis]
                        self.pos_arr[:, :, 1] = pos_y
                self.pos_arr[:, :, 0] = pos_x
            else:
                pos_y = kwargs["pos_y"]
                if pos_y.shape != self.pos_arr.shape[:2]:  # if the shape is new
                    self.pos_arr = np.zeros((*pos_y.shape, 2))
                    pos_x = np.linspace(0, 1, pos_y.shape[1])[np.newaxis, :]
                    self.pos_arr[:, :, 0] = pos_x
                self.pos_arr[:, :, 1] = pos_y

        if data is not None:
            self.data = data
            if self.shape != data.shape:    # not going to optimise this for now, you shouldn't change shape too often.
                self.shape = data.shape
                if self.pos_arr.shape != data.shape:
                    self.pos_arr = np.zeros(data.shape)
                    x, y = np.meshgrid(
                        np.linspace(0, 1, data.shape[1]), np.linspace(0, 1, data.shape[0])
                    )
                    self.pos_arr[:, :, 0] = x
                    self.pos_arr[:, :, 1] = y
                self.arrows = []
                lin_positions = self.pos_arr.reshape(self.shape[0] * self.shape[1], 2)
                lin_data = data.reshape(self.shape[0]*self.shape[1], 2)
                for index in range(self.shape[0] * self.shape[1]):
                    self.arrows.append(self.parent.arrow(
                        position=lin_positions[index], **self._data_to_kwargs(lin_data[index]), origin="center", color="black", border_width=-1)
                    )

            else:
                lin_data = data.reshape(self.shape[0]*self.shape[1], 2)
                for index, arrow in enumerate(self.arrows):
                    arrow.set_data(**self._data_to_kwargs(lin_data[index]), border_width=-1)

        if kwargs:
            if "scale_type" in kwargs:
                old_scale_type = self.scale_type
                if old_scale_type == "size":
                    for index, arrow in enumerate(self.arrows):
                        arrow.set_data(size=1)
                elif old_scale_type == "length":
                    for index, arrow in enumerate(self.arrows):
                        arrow.set_data(length=1)

                self.scale_type = kwargs["scale_type"]
                if self.scale_type == "None":
                    self.scale_type = None
            if "absolute" in kwargs:
                self.absolute = kwargs["absolute"]
            if "cmap" in kwargs:
                self.cmap = get_cmap(kwargs["cmap"])

            for color_kwarg in ["fill_color", "border_color"]:
                if color_kwarg in kwargs:
                    if is_multiple_colors(kwargs[color_kwarg]):
                        if len(kwargs[color_kwarg]) == len(self.arrows):
                            raise ValueError(f"`{color_kwarg}` should be the same length as the number of arrows, is now "
                                             f"{len(kwargs[color_kwarg])} and {len(self.arrows)}.")
                        else:
                            for index, arrow in enumerate(self.arrows):
                                arrow.set_data(**{color_kwarg: kwargs[color_kwarg][index]})
                    else:
                        for arrow in self.arrows:
                            arrow.set_data(**{color_kwarg: kwargs[color_kwarg]})

            if "border_width" in kwargs:
                border_width = kwargs["border_width"]
                if is_iter(border_width):
                    if len(border_width) == len(self.arrows):
                        raise ValueError(f"`{color_kwarg}` should be the same length as the number of arrows, is now "
                                         f"{len(border_width)} and {len(self.arrows)}.")
                    else:
                        for index, arrow in enumerate(self.arrows):
                            arrow.set_data(border_width=border_width[index])
                else:
                    for arrow in self.arrows:
                        arrow.set_data(border_width=border_width)

        if self.scale_type is None:
            if kwargs:
                new_arrow_kwargs = {}
                for kwarg in self.arrow_kwargs:
                    if kwarg in kwargs:
                        new_arrow_kwargs[kwarg] = kwargs[kwarg]
                self.current_arrow_kwargs.update(new_arrow_kwargs)
                for arrow in self.arrows:
                    arrow.set_data(**new_arrow_kwargs)
        else:
            if self.data is not None:
                if data is None:        # if data is not None, lin_data is already defined
                    lin_data = self.data.reshape(self.shape[0]*self.shape[1], 2)
                amplitude = np.sum(lin_data**2, axis=1)
                if np.any(amplitude > 0):
                    if self.scale_type == "color":
                        if not self.absolute:
                            amplitude /= np.max(amplitude)  # values between 0 and 1.
                        if self.cmap is None:
                            self.cmap = get_cmap({0: "b", 1: "r"})          # cmap is not working atm, but I believe it is
                            # fixed on my pc
                        colors = self.cmap(amplitude)
                        for index, arrow in enumerate(self.arrows):
                            arrow.set_data(c=colors[index])
                    elif self.scale_type == "length":
                        if not self.absolute:
                            amplitude = amplitude/np.max(amplitude)*2  # values between 0 and 2.
                        for index, arrow in enumerate(self.arrows):
                            arrow.set_data(length=amplitude[index])
                    elif self.scale_type == "size":
                        if not self.absolute:
                            amplitude = amplitude/np.max(amplitude)*2  # values between 0 and 2.
                        for index, arrow in enumerate(self.arrows):
                            arrow.set_data(size=amplitude[index])

    @staticmethod
    def _data_to_kwargs(arrow_data: np.ndarray):
        """
        ``arrow_data`` is here just a single arrow value, meaning this argument is ``data[i_y, i_x]``
        """
        angle = np.degrees(np.arctan2(arrow_data[1], arrow_data[0])) + 180
        return {"angle": angle}

    def _apply_pos_arr(self):
        positions = self.pos_arr.reshape(self.shape[0] * self.shape[1], 2)
        for index, arrow in enumerate(self.arrows):
            arrow.set_data(position=positions[index])
