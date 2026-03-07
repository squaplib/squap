from copy import copy
import numpy as np
from typing import Iterable, Optional

from PySide6.QtGui import QFont, QGradient, QBrush, Qt
from pyqtgraph import PlotDataItem, PlotWidget, InfiniteLine, TextItem, ImageItem, mkPen, InfLineLabel, GridItem, \
    getConfigOption, ErrorBarItem

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
            pixel_mode (bool): Whether to fix the size of each point. If ``True``, size is specified in pixels.
                If ``False``, size is specified in data coordinates. Defaults to ``True``.
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
                if other_kwargs["symbolSize"] < 0:
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

    def __init__(self, data=None, location=None, cmap=None, auto_levels=False, levels=None, axis_order="row-major",
                 border_color=None, **kwargs):        # **kwargs for aliases
        super().__init__(axisOrder="row-major")
        self.auto_levels = None         # will be updated before first usage, initial value is irrelevant.
        self.rect = None
        self.data_shape = data.shape if data is not None else None
        self.data = data            # for when cmap is given and data is not changed.
        self.cmap = None            # for when data is given and cmap is not changed
        self.set_data(data=data, location=location, cmap=cmap, auto_levels=auto_levels, levels=levels,
                      axis_order=axis_order, border_color=border_color, **kwargs)

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
