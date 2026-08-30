import numpy as np
import os.path
from typing import Iterable, Any, Optional, Callable
from argparse import ArgumentError
from inspect import signature


from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QGradient, QCursor
from pyqtgraph import PlotWidget, QtWidgets

from ..helper_funcs import get_new_kwargs, ColorType, ColorsType
from ..customisation import Font
from .curves import PlotCurve, TextCurve, InfLine, ImageCurve, GridCurve, ArrowCurve, VectorFieldCurve
from numpy.typing import NDArray


class SubplotWidget(PlotWidget):
    """
    All plotting functions are methods of this widget. e.g. :func:`squap.plot` actually redirects to
    :py:meth:`SubplotWidget.plot <SubplotWidget.plot>` of the main :class:`SubplotWidget`. When subplots are created
    with :func:`squap.subplots()` you get an ``axs`` list which contains the created :class:`SubplotWidget <SubplotWidget>`,
    so that e.g. :meth:`axs[0].plot <SubplotWidget.plot>` will create a regular plot in the first :class:`SubplotWidget`.
    """
    def __init__(self, row: int, col: int, **kwargs):
        super().__init__(**kwargs)
        self.row = row          # for merging subplots
        self.col = col
        self.curves = []        # for clearing curves
        self.mouse_leave_funcs = []

        self.enable_flicker(False)      # slows down plotting a tiny bit but makes sure no flickering occurs.

    def leaveEvent(self, event):        # allows adding function calls when the mouse leaves the widget
        super().leaveEvent(event)
        for func in self.mouse_leave_funcs:
            func()

    def base_plot(self, curve_type: str, *args, **kwargs):
        if len(args) == 1:
            kwargs["y"] = args[0]
            args = ()

        curve = PlotCurve(self, curve_type, *args, **kwargs)
        if "name" in kwargs:    # for legend
            curve.setData(name=kwargs["name"])

        self.addItem(curve)

        self.curves.append(curve)
        return curve

    def plot_text(self, text: str, pos: Iterable[float], color: ColorType = (0.8, 0.8, 0.8), angle: float = 0,
                  font: Optional[str | Font] = None, font_size: Optional[int] = None, html: Optional[str] = None,
                  text_width: Optional[int] = None, **kwargs):
        """ Displays a :class:`text object <squap.widgets.curves.TextCurve>` at coordinates pos. See :func:`squap.get_font` for more information on fonts.

        Args:
            text (str): The text to be displayed.
            pos (tuple): The position of the text in coordinates on the 2D plane.
            color (:ref:`ColorType`): Color of the text. Defaults to gray.
            border color and fill color?
            angle (float, optional): Angle at which the text is placed in degrees. Defaults to ``0``.
            font (str or Font, optional): The font of the text. Defaults to Segoe UI.
            font_size (int, optional): if set to 0 or negative, system default fontsize is used (usually 12)
            html (str, optional): The html to display, overwrites all other font arguments. Defaults to ``None``.
            text_width (int, optional): The width of the text. Todo: check how it works

        Returns:
            TextCurve: The created :class:`text object <squap.widgets.curves.TextCurve>`.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["text_width", "font", "font_size", "html"],
                                    exclude_args=["self", "kwargs", "text", "pos"])

        text_widget = TextCurve(text, pos, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases
        self.addItem(text_widget)
        return text_widget

    def imshow(self, data: Iterable | None = None, location: Iterable | None = None, cmap: Any = None,
               auto_levels: bool = False, levels=None, axis_order="row-major",
               border_color: ColorType | None = None, **kwargs):      # **kwargs for aliases
        """
        Creates an :py:class:`image <squap.widgets.curves.ImageCurve>` at location ``location``. This image consists
        of equally spaced pixels, colored according to ``data`` and ``cmap``.
        This function hasn't been tested thoroughly

        Args:
            data (:class:`np.ndarray <numpy.ndarray>`, optional): Array containing data to be shown.
                Can be shape:

                - ``(Nx, Ny, 3)``: array of colors, between ``0`` and ``1``.
                - ``(Nx, Ny, 4)``: array of colors, between ``0`` and ``1``, with alpha values.
                - ``(Nx, Ny)``: array of values between ``0`` and ``1``, corresponding to grayscale or colors corresponding to ``cmap``
                  if it is provided.

            location (tuple, optional): Location of the image. ``(location[0], location[1])`` is the bottom left coordinate, and
                ``(location[2], location[3])`` is the top right coordinate.
            cmap: Colormap from :func:`squap.get_cmap` or ``data`` argument accepted by :func:`squap.get_cmap`. If
                no cmap is given, ``data`` will be interpreted as colors.
            auto_levels (bool, optional): todo: describe
            levels (optional): todo: describe
            axis_order (bool, optional): Whether the ordering of the pixels listed in ``data`` is ``"row-major"`` or
                ``"col-major"``. Todo: test if it does anything.
            border_color (:ref:`ColorType`, optional): Color of the border around the image. Defaults to ``None``, meaning no border.
            todo: border thickness?

        Returns:
            ImageCurve: The created image curve.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["location", "cmap"],
                                    exclude_args=["self", "args", "kwargs"])

        img = ImageCurve(**new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases
        self.addItem(img)
        return img

    def plot(
            self, *args, color: ColorsType = "y", width: int = 1, dashed: bool = False,
            dash_pattern: Optional[Iterable[int]] = None, connect: str | NDArray = "auto",
            gradient: Optional[QGradient] = None, line_style: Optional[str] = None, antialias: bool = True,
            auto_downsample: bool = False, downsample: int = 1, downsample_method: str = "mean",
            skip_finite_check: bool = False, **kwargs
    ) -> 'PlotCurve':
        """
        Creates a new :class:`plot curve <squap.widgets.curves.PlotCurve>`, and calls
        :meth:`set_data <squap.widgets.curves.PlotCurve.set_data>` with the other (keyword) arguments.

        Args:
            *args: Provide ``x`` and ``y``, just ``y``, or no data at all. Data can also be passed as keyword arguments.
            color (:ref:`ColorsType`): The color of the line. Default is ``"y"`` (yellow). Can also be a gradient
                (created with :func:`squap.get_gradient`).
            width (int): Width of the plot line. Default is ``1``.
            dashed (bool): If ``True``, draws a dashed line between the points (for more options see dash_pattern).
                Default is ``False``.
            dash_pattern (list, optional): How the dashes are spaced. For example, if ``dash_pattern`` is ``[16, 16, 4, 16]``, the pattern
                will be: one dash of 16 pixels long, then a space of 16 pixels long, then a dash of 4 pixels long and then
                a dash of 16 pixels long. This pattern is then repeated. This should be a list with a length that is an
                integer multiple of 2. Setting ``dash_pattern`` will also automatically set ``dashed`` to ``True``. Defaults to ``[16, 16]``.
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
            gradient (:class:`QGradient <PySide6.QtGui.QGradient>`, optional): gradient of the line. Use :func:`squap.get_gradient` to get the gradient. The
                gradient can be seen as a 2D image of a gradient which appears at each pixel that lies on the line.
                When ``style`` of the gradient is set to ``"horizontal"`` or ``"vertical"``, or ``"radial"`` without providing
                ``position``, the bounds of the gradient will be automatically determined when
                :meth:`set_data <squap.widgets.curves.PlotCurve.set_data>` is called, which can decrease performance. So, specify ``position`` for
                optimal performance. Default is ``None``.
            line_style (optional, str): todo: some presets for simplicity, ``ls`` is also allowed instead of ``line_style``.
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
                for :data:`NaN <numpy.nan>` values. If set to ``True``, and :data:`NaN <numpy.nan>` values exist,
                unpredictable behavior will occur. The data may
                not be displayed or the plot may take a significant performance hit. Defaults to ``False``.
            **kwargs: Can contain aliases and the following:
                - ``x``: You can provide ``x`` as keyword argument as well.
                - ``y``: You can provide ``y`` as keyword argument as well.

        Returns:
            :class:`PlotCurve <squap.widgets.curves.PlotCurve>`: The generated curve.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["dash_pattern", "gradient", "line_style"],
                                    exclude_args=["self", "args", "kwargs"])

        return self.base_plot("plot", *args, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

    def scatter(
            self, *args, color: ColorsType = "y", size: int | Iterable[int] = 7, edge_width: int | Iterable[int] = -1,
            edge_color: ColorsType = "white", pixel_mode: bool = True, downsample: int = 1, downsample_method: str = "mean", auto_downsample: bool = False,
            antialias: bool = True, **kwargs
    ) -> 'PlotCurve':
        """
        Creates a new :class:`scatter curve <squap.widgets.curves.PlotCurve>`, and calls
        :meth:`set_data <squap.widgets.curves.PlotCurve.set_data>` with the other arguments.
        If both ``x`` and ``y`` are provided, you can set them together using ``scatter(x, y, ...)``.
        If only ``y`` is provided using ``scatter(y, ...)``,
        ``x`` is set as the index of ``y``. ``x`` and ``y`` can also be passed as keyword arguments by doing ``scatter(x=x, ...)``,
        ``scatter(y=y)`` or ``scatter(x=x, y=y, ...)``. Furthermore, you can include additional keyword
        arguments such as color and size to customize the appearance of the curve.

        Args:
            *args: Provide ``x`` and ``y``, just ``y``, or no data at all. Data can also be passed as keyword arguments.
            color (:ref:`ColorType`): the color of the points. See :ref:`ColorsType` for allowed values.
                If a list of colors is passed, it should be the same length as ``x`` and ``y``.
            size (int or list of int): The size of the scatter plot points. Also accepted as ``s``. Default is ``7``.
            edge_width (int or list of int): Width of the edge around each point. Default is ``-1`` (no edge).
            edge_color (:ref:`ColorsType`): Color of the edge around each point. Default is white.
            pixel_mode (bool): Whether to fix the size of each point. If ``True``, size is specified in pixels.
                If ``False``, size is specified in data coordinates. Defaults to ``True``.
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

            kwargs: Can contain the following:
                - ``x``: You can provide ``x`` as keyword argument as well.
                - ``y``: You can provide ``y`` as keyword argument as well.

        Returns:
            :class:`PlotCurve <squap.widgets.curves.PlotCurve>`: The generated curve.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self", "args", "kwargs"])

        return self.base_plot("scatter", *args, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

    def errorbar(self, *args, x_err=None, y_err=None, color: ColorType = "y",
                 width: int = 1, errorbar_width: int = 1, beam_size: float = 0, dashed: bool = False,
                 dash_pattern: Iterable[int] = None, connect: str = "auto", gradient: Optional[QGradient] = None,
                 line_style: Optional[str] = None, antialias: bool = True, auto_downsample: bool = False,
                 downsample: int = 1, downsample_method: str = "mean", skip_finite_check: bool = False, **kwargs
         ) -> 'PlotCurve':
        """
        Creates a new :class:`errorbar curve <squap.widgets.curves.PlotCurve>`, and calls
        :meth:`set_data <squap.widgets.curves.PlotCurve.set_data>` with the other (keyword) arguments.


        Args:
            *args: For providing ``x`` and ``y``. (Can also be provided as keyword arguments). ``x`` and ``y`` must be the same
                length. If only one argument is provided, it is interpreted as ``y`` and ``x`` is set
                to the index of ``y``.
            x_err: Size of the errorbar at each x value. Can be the following types:

                - ``None``: No error in the x-direction.
                - ``float``: x-error at all points.
                - Iterable of same size as ``x``: x-error at each point.
                - Iterable of size `(Nx, 2)`: ``x_err[i, 0]`` is the error on the left at each point, and ``x_err[i, 1]`` is the error on the right at each point ``i``.

                Defaults to ``None``.

            y_err: Same as ``x_err`` but for ``y``.
            color (:ref:`ColorType`): Color of the line and errorbars. Default is ``"y"`` (yellow). Can also be a gradient (see
                :func:`squap.get_gradient`). If the color of the line and of the errorbar should be different, provide both
                ``line_color`` and ``errorbar_color``.
            width (int): Width of the plot line. Default is ``1``. Does not affect the width of the errorbars.
            errorbar_width (int): Width of the errorbar lines. Default is ``1``.
            beam_size (float): Size of the bars at the ends of the errorbar lines. Default is ``0``.
            dashed (bool): If ``True``, draws a dashed line between the points (for more options see ``dash_pattern``).
                Defaults to ``False``.
            dash_pattern (list, optional): How the dashes are spaced. For example, if ``dash_pattern`` is ``[16, 16, 4, 16]``, the pattern
                will be: one dash of 16 pixels long, then a space of 16 pixels long, then a dash of 4 pixels long and then
                a dash of 16 pixels long. This pattern is then repeated. This should be a list with a length that is an
                integer multiple of 2. Setting ``dash_pattern`` will also automatically set ``dashed`` to ``True``. Defaults to ``[16, 16]``.
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
            line_style (str, optional): todo: some presets for simplicity, `ls` is also allowed instead of `line_style`.
            gradient (:class:`QGradient <PySide6.QtGui.QGradient>`, optional): gradient of the line. Use :func:`squap.get_gradient` to get the gradient. The
                gradient can be seen as a 2D image of a gradient which appears at each pixel that lies on the line.
                When ``style`` of the gradient is set to ``"horizontal"`` or ``"vertical"``, or ``"radial"`` without providing
                ``position``, the bounds of the gradient will be automatically determined when :meth:`set_data <squap.
                plot_widget.PlotCurve.set_data>` is called, which can decrease performance. So, specify ``position`` for
                optimal performance.
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

            **kwargs: Can contain the following:
                - `x`: You can provide `x` as keyword argument as well.
                - `y`: You can provide `y` as keyword argument as well.
                - `line_color`: For seperating errorbar and line color.
                - `error_color`: For seperating errorbar and line color.
                - `line_width`: For seperating errorbar and line width.
                - `error_width`: For seperating errorbar and line width.

        Returns:
             :class:`PlotCurve <squap.widgets.curves.PlotCurve>`: The generated curve. The errorbar curve is
             technically located at :class:`ErrorbarCurve <squap.widgets.curves.ErrorbarCurve>`, but everything
             can be set with just :meth:`PlotCurve.set_data() <squap.widgets.curves.PlotCurve.set_data>`.
        """

        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["errorbar_color", "errorbar_width", "dash_pattern", "gradient",
                                                 "line_style"],
                                    exclude_args=["self", "args", "kwargs"])

        return self.base_plot("plot", *args, **new_kwargs, **kwargs)

    def inf_dline(self, pos: float | tuple[float, float], angle: float = 45, color: ColorType = "y", width: int = 1,
                  dashed: bool = False, dash_pattern: Optional[Iterable[int]] = None, line_style: Optional[str] = None,
                  movable: bool = False, bounds: Optional[Iterable[int]] = None, span: tuple = (0, 1),
                  line_movable: Optional[bool] = None, label: bool = False, label_text: str = "{value}",
                  label_movable: Optional[Iterable[int]] = None, label_position: float = 0.5,
                  label_anchors: Optional[list[tuple]] = None, hover_color: ColorType = "red", hover_width: int = 1,
                  name: Optional[str] = None, **kwargs):
        """
        Creates an infinite line with any orientation and add it to the view.

        Args:
            pos (float or tuple): A position through which the line runs. When ``angle`` is ``0`` or ``90`` this can be a
                single value: the y- or x-value of the line respectively.
            angle (float): The angle of the line in degrees. ``0`` is horizontal, ``90`` is vertical. Default is ``45``.
            color (:ref:`ColorType`): Color of the line. Default is ``"y"`` (yellow). Can also be a :func:`gradient <squap.get_gradient>`.
            width (int): Width of the plot line. Default is ``1``.
            dashed (bool): If ``True``, draws a dashed line between the points (for more options see dash_pattern).
                Default is ``False``.
            dash_pattern (list, optional): How the dashes are spaced. For example, if ``dash_pattern`` is ``[16, 16, 4, 16]``, the pattern
                will be: one dash of 16 pixels long, then a space of 16 pixels long, then a dash of 4 pixels long and then
                a dash of 16 pixels long. This pattern is then repeated. This should be a list with a length that is an
                integer multiple of 2. Setting ``dash_pattern`` will also automatically set ``dashed`` to ``True``. Defaults to ``[16, 16]``.
            line_style (str): todo: some presets for simplicity, `ls` is also allowed instead of `line_style`.
            movable (bool, optional): Whether the line (and label if it exists) is movable or not. Default is False.
            bounds (tuple, optional): Optional (min, max) bounding values. Bounds are only valid if the line is
                vertical or horizontal. Default is no bounds.
            span (tuple): The length of the line on screen. The first number is how far it extends to todo: complete
            line_movable (bool, optional): Whether the line is movable or not. Overwrites `movable` if changed.
                Default is None.
            label (bool): The label doesn't work completely yet, I think this is due to pyqtgraph itself. Will look into
                this later. If ``True``, a label is added to the line. Default is ``False``.
            label_text (str): The text that is shown on the label. ``{value}`` can be used inside the string, which will be
                replaced by the lines current position. Default is ``"{value}"``.
            label_movable (bool, optional): Whether the label is movable or not. Overwrites ``movable`` if changed.
                Default is None.
            label_position (float): The relative position (between ``0.0`` and ``1.0``) of this label within the view box and
                along the line. Default is ``0.5``, meaning in the middle.
            label_anchors (list, optional): todo: write
            hover_color (:ref:`ColorType`): Color to use when the mouse cursor hovers over the line. Only used when ``movable=True``.
                Default is red.
            hover_width (int): Width to use when the mouse cursor hovers over the line. Default is ``1``.
            name (str, optional): Name of the item (for the legend).
            **kwargs: Some aliases are allowed.

        Returns:
            InfLine: The generated line.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["dash_pattern", "line_style"],
                                    exclude_args=["self", "pos", "kwargs"])

        line = InfLine(pos, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

        self.addItem(line)
        self.curves.append(line)
        return line

    def inf_hline(self, pos: float | tuple[float, float], color: ColorType = "y", width: int = 1,
                  dashed: bool = False, dash_pattern: Optional[Iterable[int]] = None, line_style: Optional[str] = None,
                  movable: bool = False, bounds: Optional[Iterable[int]] = None, span: tuple = (0, 1),
                  line_movable: Optional[bool] = None, label: bool = False, label_text: str = "{value}",
                  label_movable: Optional[Iterable[int]] = None, label_position: float = 0.5,
                  label_anchors: Optional[list[tuple]] = None, hover_color: ColorType = "red", hover_width: int = 1,
                  name: Optional[str] = None, **kwargs):
        """
        This function is used to create a horizontal infinite line and add it to the view. This function is the same as
        :func:`inf_dline(pos, angle=90, ...) <squap.inf_dline>` but instead the default ``label_text`` is now ``"y={value}"``.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["dash_pattern", "line_style"],
                                    exclude_args=["self", "pos", "kwargs"])

        line = InfLine(pos, angle=0, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

        self.addItem(line)
        self.curves.append(line)
        return line

    def inf_vline(self, pos: float | tuple[float, float], color: ColorType = "y", width: int = 1,
                  dashed: bool = False, dash_pattern: Optional[Iterable[int]] = None, line_style: Optional[str] = None,
                  movable: bool = False, bounds: Optional[Iterable[int]] = None, span: tuple = (0, 1),
                  line_movable: Optional[bool] = None, label: bool = False, label_text: str = "{value}",
                  label_movable: Optional[Iterable[int]] = None, label_position: float = 0.5,
                  label_anchors: Optional[list[tuple]] = None, hover_color: ColorType = "red", hover_width: int = 1,
                  name: Optional[str] = None, **kwargs):
        """
        This function is used to create a horizontal infinite line and add it to the view. This function is the same as
        :func:`inf_dline(pos, angle=90, ...) <squap.inf_dline>` but instead the default ``label_text`` is now ``"x={value}"``.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["dash_pattern", "line_style"],
                                    exclude_args=["self", "pos", "kwargs"])

        line = InfLine(pos, angle=90, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

        self.addItem(line)
        self.curves.append(line)
        return line

    def grid(self, tick_spacing: Optional[tuple | float] = None, color: Optional[ColorType] = None, width: int = 1,
             **kwargs):
        """
        This function is used to create a :class:`grid <squap.widgets.curves.GridCurve>` and add it to view. Todo: improve
        Use :func:`squap.show_grid` for simple use-cases.

        Args:
            tick_spacing(tuple or float, optional): Set the grid spacing. When set to ``None`` grid line distance is
                chosen automatically. When an iterable is given, give x- and y-spacing. When one value is given, this value
                is used for both x and y. For more complex scaling you can set the x- and y-spacing on different scales.
                Eg. passing ``([1, 100], None)`` will mean x-spacing is automatically determined to be either 1 or 100,
                and y-spacing is completely automatic. Replacing ``[1, 100]`` by ``[1, 100, None]`` will mean it can be 1 or
                100 depending on zoom level, or it can be completely automatic for anything outside this range.
            color (:ref:`ColorType`, optional): Color of the lines. Defaults to the config foreground color.
            width (int): Width of the plot line. Default is ``1``.
            **kwargs: Some aliases are allowed.

        Returns:
            GridCurve: The generated :class:`grid <squap.widgets.curves.GridCurve>`.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self", "kwargs"])

        grid = GridCurve(**new_kwargs, **kwargs)

        self.addItem(grid)
        self.curves.append(grid)
        return grid

    def arrow(self, angle: float = 0., size: float = 1., position: tuple[float, float] = (0., 0.),
              fill_color: ColorType = "white", border_color: ColorType = "blue", border_width: float = -1,
              origin: str = "tip", pixel_mode: bool = True, head_length: float = 20,
              head_width: Optional[float] = None, tip_angle: float = 60., base_angle: float = 0.,
              tail_length: Optional[float] = 50., tail_width: float = 6., length: float = 1., **kwargs):
        """
        Creates a new :class:`arrow object <squap.widgets.curves.ArrowCurve>`, and calls
        :meth:`set_data <squap.widgets.curves.ArrowCurve.set_data>` with the other (keyword) arguments.
        To add a vector field see :meth:`squap.vector_field`, and for an arrow
        pointing to a location on a curve see (Not implemented yet).

        Args:
            angle (float): Orientation of the arrow in degrees. Default is 0.; arrow pointing to the left.
            size (float): Relative size of the arrow. Change to proportionally scale all relevant parameters. Use
                :meth:`arrow.get_data() <squap.widgets.curves.ArrowCurve.get_data>` to see the values of
                these parameters.
            position (tuple of float): Position of the arrow in coordinates. Defaults to ``(0, 0)``. Which part of the
                arrow is placed at this position is controlled by ``origin``.
            fill_color (:ref:`ColorType`): The color of the arrow. Defaults to ``"white"``.
            border_color (:ref:`ColorType`): The color of the border around the arrow. Defaults to ``"blue"``
                (but the border is not visible by default).
            border_width (float): The width of the border around the arrow. Defaults to ``-1`` meaning it is disabled.

            origin (str): Which part of the arrow is placed at ``location``; this point also acts as the
                arrow's center of rotation. One of:

                - ``"tip"``: the tip of the arrow.
                - ``"center"``: the center of the arrow.
                - ``"tail"``: the tail of the arrow.

                Defaults to ``"tip"``. Is only implemented for pxMode=False.

            pixel_mode (bool): If ``True``, parameters are specified in pixels. If ``False``, parameters are
                specified in data coordinates. Defaults to ``True``.
            head_length (float): Length of the arrow head, from tip to base. Default is ``20``.
            head_width (float, optional): Width of the arrow head at its base. If `head_width` is specified, it
                overrides ``tip_angle``.
            tip_angle (float): Angle of the tip of the arrow in degrees. Smaller values make a ‘sharper’ arrow.
                Default is ``60``.
            base_angle (float): Angle of the base of the arrow head. Default is ``0``, which means that the base of the
                arrow head is perpendicular to the arrow tail.
            tail_length (float, optional): Length of the arrow tail, measured from the base of the arrow head to the
                end of the tail. If this value is None, no tail will be drawn. Default is ``50``.
            tail_width (float): Width of the tail. Default is ``6``.
            length (float): Relative length of the arrow. Change to proportionally scale all relevant parameters. Use
                :meth:`arrow.get_data() <squap.widgets.curves.ArrowCurve.get_data>` to see the values of these
                parameters.

        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["head_width"],
                                    exclude_args=["self", "kwargs"])

        arrow = ArrowCurve(view_box=self.getPlotItem().getViewBox(), **new_kwargs, **kwargs)

        self.addItem(arrow)
        self.curves.append(arrow)       # I am not sure if this should also happen if it is part of a vector field.
        return arrow

    def vector_field(self, data: np.ndarray, pos_x: Optional[np.ndarray] = None, pos_y: Optional[np.ndarray] = None,
                     scale_type: Optional[str] = None, size: float = 1., pixel_mode: bool = True,
                     fill_color: ColorsType = "yellow", border_color: ColorsType = "blue",
                     border_width: float | list[float] = -1, cmap: Optional[Any] = None, absolute: bool = False,
                     head_length: float = 4., head_width: Optional[float] = None, tip_angle: float = 60.,
                     base_angle: float = 0., tail_length: Optional[float] = 10., tail_width: float = 1.2,
                     **kwargs):
        """
        Creates a new :class:`vector field <squap.widgets.curves.VectorFieldCurve>`, and calls
        :meth:`set_data <squap.widgets.curves.VectorFieldCurve.set_data>` with the other (keyword) arguments.
        Accepts most arguments accepted by :meth:`squap.arrow`, that form a basis arrow. All arrows
        are based on this basis arrow, and scaled due to the size of the vector field according to ``scale_type``.
        To add a single arrow see :meth:`squap.arrow`, and for an arrow pointing to a location on a curve
        see (Not implemented yet).

        Args:
            data (:class:`np.ndarray <numpy.ndarray>`): The vector field which is displayed. It should be
                shape ``(Ny, Nx, 2)``.
            pos_x (:class:`np.ndarray <numpy.ndarray>`, optional): The x-positions at which each vector is shown.
                Shape should be ``(Ny, Nx)``,  for example obtained from :func:`np.meshgrid <numpy.meshgrid>`.
                Defaults to evenly spaced points between 0 and 1.
            pos_y (:class:`np.ndarray <numpy.ndarray>`, optional): The y-positions at which each vector is shown.
                Shape should be ``(Ny, Nx)``,  for example obtained from :func:`np.meshgrid <numpy.meshgrid>`.
                Defaults to evenly spaced points between 0 and 1.
            scale_type (str): How the amplitude of the vector field is shown.
                It should be one of the following:

                - ``None`` or ``"None"``: The amplitude of the vector field has no visual effect.
                - ``"length"``: The amplitude of the vector field changes the length of the arrows, but not the width.
                - ``"size"``: The amplitude changes the length and width of the arrows.
                - ``"color"``: The amplitude changes the color according to the given ``cmap``.

                Defaults to ``"length"``.
            size (float): Increases or decreases the size of all arrows. Defaults to ``1``.
            pixel_mode (bool): If ``True``, parameters are specified in pixels. If ``False``, parameters are
                specified in data coordinates. Defaults to ``True``.

            fill_color (:ref:`ColorType`): The color of the arrow. Defaults to ``"white"``.
            border_color (:ref:`ColorType`): The color of the border around the arrow. Defaults to ``"blue"``
                (but the border is not visible by default).
            border_width (float): The width of the border around the arrow. Defaults to ``-1`` meaning it is disabled.

            cmap: Colormap from :func:`squap.get_cmap` or ``data`` argument accepted by :func:`squap.get_cmap`, which
                is used if scale_type is set to ``"color"``.
            absolute (bool): If ``False`` normalizes the amplitude of the field. If ``True``, uses the absolute value.
                When set to ``False``, for ``scale_type = "color"`` the amplitudes are scaled so that the maximum value
                is 1, for ``length`` and ``"size"`` the amplitudes are scaled so that the maximum amplitude
                is 2. Has no affect when ``scale_type`` is set to ``None``. Defaults to ``False``.
                Setting ``absolute`` to ``True`` can cause unexpected behaviour when ``scale_type`` is set
                to ``"color"``.

            head_length (float): Length of the arrow head, from tip to base. Default is ``20``.
            head_width (float, optional): Width of the arrow head at its base. If `head_width` is specified, it
                overrides ``tip_angle``.
            tip_angle (float): Angle of the tip of the arrow in degrees. Smaller values make a ‘sharper’ arrow.
                Default is ``60``.
            base_angle (float): Angle of the base of the arrow head. Default is ``0``, which means that the base of the
                arrow head is perpendicular to the arrow tail.
            tail_length (float, optional): Length of the arrow tail, measured from the base of the arrow head to the
                end of the tail. If this value is None, no tail will be drawn. Default is ``50``.
            tail_width (float): Width of the tail. Default is ``6``.

        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["pos_x", "pos_y", "cmap"],
                                    exclude_args=["self", "kwargs"])

        curve = VectorFieldCurve(self, **new_kwargs, **kwargs)
        self.curves.append(curve)
        return curve

    def lock_zoom(self, curves: 'Iterable[PlotCurve]'):
        """
        Locks zoom onto current range of specified :class:`curves <squap.widgets.curves.PlotCurve>`. Works only
        if they are normal :class:`curves <squap.widgets.curves.PlotCurve>` with x- and y- data.

        Args:
            curves (list of :class:`curves <squap.widgets.curves.PlotCurve>`):
                :class:`curves <squap.widgets.curves.PlotCurve>` on which the zoom should lock

        """
        x_min, x_max, y_min, y_max = [], [], [], []

        for curve in curves:
            x, y = curve.getData()
            x_min.append(min(x))
            x_max.append(max(x))
            y_min.append(min(y))
            y_max.append(max(y))
        self.set_xlim(min(x_min), max(x_max))
        self.set_ylim(min(y_min), max(y_max))

    def set_xlim(self, x_min: float, x_max: float):
        """
        Sets the view range in the x direction.

        Args:
            x_min (float): minimum x value for the plot range
            x_max (float): maximum x value for the plot range
        """
        self.setXRange(x_min, x_max)

    def set_ylim(self, y_min: float, y_max: float):
        """
        Sets the view range in the x direction.

        Args:
            y_min (float): minimum y value for the plot range
            y_max (float): maximum y value for the plot range
        """
        self.setYRange(y_min, y_max)

    def xlim(self) -> tuple[float]:
        """
        Returns current xlim.
        """
        return tuple(self.getViewBox().viewRange()[0])

    def ylim(self) -> tuple[float]:
        """"
        Returns current ylim.
        """
        return tuple(self.getViewBox().viewRange()[1])

    def set_xlabel(self, label: str, unit: str = "", right_side: bool = False):
        """
        Sets a label on the x-axis.

        Args:
            label (str): Text that gets displayed on the x-axis.
            unit (str): Unit can be added as seperate argument.
            right_side (bool): The text can be displayed on the opposite site too by setting this parameter to ``True``.
        """
        kwargs = {"units": unit} if unit else {}
        if right_side:
            self.setLabel("right", label, **kwargs)
        else:
            self.setLabel("left", label, **kwargs)

    def set_ylabel(self, label: str, unit: str = "", top_side: bool = False):
        """
        Sets a label on the y-axis.

        Args:
            label (str): Text that gets displayed on the y-axis.
            unit (str): Unit can be added as seperate argument.
            top_side (bool): The text can be displayed on the opposite site too by setting this parameter to ``True``.
        """
        kwargs = {"units": unit} if unit else {}
        if top_side:
            self.setLabel("top", label, **kwargs)
        else:
            self.setLabel("bottom", label, **kwargs)

    # Wrapper that changes name and docstring only. Done like this for consistent documentation.
    def show_grid(self, x: Optional[bool] = None, y: Optional[bool] = None, alpha: Optional[float] = None):
        """
        Show or hide the grid for either axis. For more detailed control see :func:`squap.grid`.

        Args:
            x (bool, optional): Show grid on the x-axis, starts off as ``False``.
            y (bool, optional): Show grid on the y-axis, starts off as ``False``.
            alpha (float, optional): Opacity of the grid, float between ``0.`` and ``1.``.
        """
        self.showGrid(x, y, alpha)

    def enable_flicker(self, enable=True):
        """This function can be called to optimise plotting, but can cause flickering at high framerate.
        """
        if not enable:
            self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        else:
            self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)

    def enable_autoscale(self, axis: Optional[str] = None, enable: bool = True, x: Optional[bool] = None,
                         y: Optional[bool] = None):
        """
        Enables (or disables) auto-range for ``axis``, which may be ``"x"``, ``"y"``, or ``"xy"`` for both (if ``axis`` is omitted, both
        axes will be changed).
        When enabled, the axis will automatically rescale when items are added/removed or change their shape.
        The argument ``enable`` may optionally be a float (``0.0`` to ``1.0``) which indicates the fraction of the data that should
        be visible.
        Also allows setting ``x`` and or ``y`` to ``True`` for simpler interface.

        Args:
            axis (str, optional): Axis to autoscale. Can be ``"x"``, ``"y"``, or ``"xy"``, or ``None`` for both. Defaults to ``None``.
            enable (bool): Whether to enable or disable. Defaults to ``True``.
            x (bool, optional): optional simpler interface. Setting this to ``True`` enables autoscaling in the x-direction.
                Defaults to ``None``.
            y (bool, optional): optional simpler interface. Setting this to ``True`` enables autoscaling in the y-direction.
                Defaults to ``None``.
        """
        self.enableAutoRange(axis, enable, x, y)        # None as arg is fine

    def disable_autoscale(self, axis: Optional[str] = None, x: Optional[bool] = None, y: Optional[bool] = None):
        """Disables auto-scale. (Equivalent to :func:`enable_autoscale(enable=False) <squap.enable_autoscale>`)"""
        self.enableAutoRange(axis, enable=False, x=x, y=y)

    def enable_autopan(self, axis: Optional[str] = None, enable: bool = True, x: Optional[bool] = None,
                         y: Optional[bool] = None):
        """
        Enables (or disables) autopan for ``axis``, which may be ``"x"``, ``"y"``, or ``"xy"`` for both (if ``axis`` is omitted, both
        axes will be changed). Only does something when autoscaling is enabled.
        When enabled, the axis will automatically pan to objects in the plot meaning the zoom level stays the same but the offset changes.
        The argument ``enable`` may optionally be a float (``0.0`` to ``1.0``) which indicates the fraction of the data that should
        be visible.
        Also allows setting ``x`` and or ``y`` to ``True`` for simpler interface.

        Args:
            axis (str, optional): Axis to autoscale. Can be ``"x"``, ``"y"``, or ``"xy"``, or ``None`` for both. Defaults to ``None``.
            enable (bool): Whether to enable or disable. Defaults to ``True``.
            x (bool, optional): optional simpler interface. Setting this to ``True`` enables autoscaling in the x-direction.
                Defaults to ``None``.
            y (bool, optional): optional simpler interface. Setting this to ``True`` enables autoscaling in the y-direction.
                Defaults to ``None``.
        """
        kwargs = {}
        if axis is not None:
            if "x" in axis:
                x = enable
            if "y" in axis:
                y = enable
        else:
            if x is None and y is None:
                x, y = enable, enable
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y

        print(kwargs)
        self.setAutoPan(**kwargs)

    def disable_autopan(self, axis: Optional[str] = None, x: Optional[bool] = None,
                       y: Optional[bool] = None):
        """Disables auto-scale. (Equivalent to :func:`enable_autopan(enable=False) <squap.enable_autopan>`)"""
        self.enable_autopan(axis, enable=False, x=x, y=y)

    def legend(self):
        """
        Call before creating the curves! todo: test

        """
        self.addLegend()

    def set_title(self, text: str | Any):
        """
        Sets title to ``str(text)``.

        Args
            text (str or Any): title, can be a string or any argument accepted by ``str``
        """
        self.setTitle(text)

    def remove_curve(self, curve: QWidget):
        """Removes an item from the plot, usually a curve."""
        self.removeItem(curve)

    def on_mouse_click(self, func: Callable, pixel_mode: bool = False):
        """
        Bind function to run on mouse click. As arguments it gets the position of the mouse; in pixels if ``pixel_mode`` is
        set to ``True`` and in coordinates if set to ``False``. The second argument that is passed is which mouse button is clicked.

        Args:
            func (:term:`callable`): The function that is called when the mouse is clicked. The function can take up to 2 arguments:
                the first is the mouse position, the second is the pyqtgraph internal event for more advanced usage.
            pixel_mode (bool): whether to return pixels from the top left (``True``), or coordinates (``False``).
                Defaults to ``False``.
        todo: check all MouseClickEvent options, and check with middle mouse button
        todo: automatically determine which ax.
        """
        params = signature(func).parameters
        has_var_args = any(
            param.kind == param.VAR_POSITIONAL
            for param in params.values()
        )
        n_args = 2 if has_var_args else len(params)

        if len(params) > 2:
            raise ArgumentError(func, f"func should take one or two arguments, but currently takes "
                                      f"{len(signature(func).parameters)} arguments.")

        if pixel_mode:
            def mouse_func(event):
                pos = event.scenePos().toTuple()
                args = ([pos, event][i] for i in range(n_args))  # handles 0, 1 or 2 n_args
                func(*args)

        else:
            def mouse_func(event):
                pos = event.scenePos()
                plot_pos = self.getViewBox().mapSceneToView(pos).toTuple()
                print(event, pos, plot_pos)
                args = ([plot_pos, event][i] for i in range(n_args))  # handles 0, 1 or 2 n_args
                func(*args)

        self.scene().sigMouseClicked.connect(mouse_func)

    def on_mouse_move(self, func: Callable, pixel_mode: bool = False):
        """Bind a function to mouse move.

        Args:
            func (:term:`callable`): The function that is called when the mouse is moved. The function receives the mouse position
                as an argument.
            pixel_mode (bool): whether to return pixels from the top left (``True``), or coordinates (``False``).
                Defaults to ``False``.
        """
        params = signature(func).parameters
        has_var_args = any(
            param.kind == param.VAR_POSITIONAL
            for param in params.values()
        )
        n_args = 1 if has_var_args else len(params)

        if len(params) > 1:
            raise ArgumentError(func, f"func should take one or two arguments, but currently takes "
                                      f"{len(signature(func).parameters)} arguments.")

        if pixel_mode:
            def mouse_func(pos_pixel):
                pos = pos_pixel.toTuple()
                if n_args == 0:
                    func()
                else:
                    func(pos)
        else:
            def mouse_func(pos_pixel):
                plot_pos = self.getViewBox().mapSceneToView(pos_pixel).toTuple()
                if n_args == 0:
                    func()
                else:
                    func(plot_pos)

        self.scene().sigMouseMoved.connect(mouse_func)

    def on_mouse_leave(self, func: Callable):
        """Calls the function ``func`` when the mouse leaves the widget."""
        self.mouse_leave_funcs.append(func)

    def get_mouse_pos(self, pixel_mode=False) -> tuple:
        """Get the position of the mouse cursor on the plot, either as pixels from the top left, or as coordinates.

        Args:
            pixel_mode (bool): whether to return pixels from the top left (``True``), or coordinates (``False``).
                Defaults to ``False``.
        Returns:
            tuple: The coordinates of the mouse cursor on the plot.
        """

        pos = self.mapFromGlobal(QCursor.pos())
        if pixel_mode:
            return pos.toTuple()
        else:
            return self.getViewBox().mapSceneToView(pos).toTuple()
