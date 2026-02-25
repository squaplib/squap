from .helper_funcs import get_single_color, Font, ColorType, get_new_kwargs
from typing import Iterable, Optional
from PySide6.QtGui import QLinearGradient, QRadialGradient, QConicalGradient, QGradient, QCursor, QGuiApplication
from PySide6.QtCore import QPointF
from matplotlib import colors
from pyqtgraph import colormap
import numpy as np


def get_font(font_name: str = "Segoe UI", font_size: Optional[int] = None, bold: bool = False,
                 italic: bool = False, underline: bool = False, strikethrough: bool = False, overline: bool = False,
                 kerning: bool = False, stretch: int = 100, letter_spacing: float = .0, word_spacing: float = .0,
                 **kwargs) -> Font:
    """Get font object. Usually names are allowed when a font is required as an argument, but this function creates
    more complex fonts

    Args:
        font_name (str): Name of the font. Can be any font on your computer. Defaults to ``"Segoe UI"``.
            Aliases: ``font``, ``fn``.
        font_size (int): Font size. Defaults to ``None``. This usually means the ``font_size`` is 12 todo: check
            Aliases: ``size``, ``fs``.
        bold (bool): Whether to make the font bold. Defaults to ``False``.
        italic (bool): Whether to make the font italic. Defaults to ``False``.
        underline (bool): Whether to give the font underline. Defaults to ``False``.
        strikethrough (bool): Whether to make the font strikethrough. Defaults to ``False``. Alias: ``strikeout``.
        overline (bool): Whether to give the font overline. Defaults to ``False``.
        kerning (bool): Whether to draw the font with kerning. If kerning is enabled the text is drawn a bit more
            compactly. Defaults to ``False``.
        stretch (int): Stretch factor as percentage. Eg. ``100`` is normal, ``200`` is twice as wide. Default is ``100``.
        letter_spacing (float): Extra spacing between letters in pixels. Defaults to ``0.0``. Alias: ``ls``.
        word_spacing (float): Extra spacing between words in pixels. Defaults to ``0.0``. Alias: ``ws``.
        **kwargs: Aliases. See argument description for allowed aliases.
        todo: setFixedPitch?, setLetterSpacing?, setWordSpacing?
    """
    new_kwargs = get_new_kwargs(locals(),
                                none_kwargs=["font_size"],
                                exclude_args=["kwargs"])

    return Font(**new_kwargs)


def get_gradient(cmap: str | colors.Colormap | Iterable | dict, style: str = "horizontal",
                 position: Optional[Iterable] = None, extend: str = "pad", resolution: int = 256) -> QGradient:
    """Obtain a gradient. Gradients can sometimes be used instead of normal colors.

    The gradient can be seen as a 2D image of a gradient placed depending on ``position``. Only the parts are shown at
    each pixel that is drawn by eg. a plot line. When `style` of the gradient is set to ``"horizontal"`` or ``"vertical"``, or
    ``"radial"`` without providing ``position``, the bounds of the gradient will be automatically determined when
    :meth:`curve.set_data <squap.widgets.plot_widget.PlotCurve.set_data>` is called. Specify ``position`` for optimal performance.

    Args:
        cmap (str, dict, list or Colormap): The colormap used as gradient. Can either be a string, a dictionary,
            a list of colors or an instance of `matplotlib.colors.Colormap`:

            - ``str``: Any matplotlib colormap name. When a colormap exists in both matplotlib and cmasher,
              matplotlib takes priority. Prefix with ``"mpl_"`` or ``"cmasher_"`` to select explicitly.
            - ``dict``: Maps positions (0–1) to colors. ``cmap[0]`` and ``cmap[1]`` are the start and end,
              with linear interpolation between any intermediate points.
            - ``list``: Colors equally spaced between 0 and 1, with linear interpolation between them.
            - ``Colormap``: Used directly.

        style (str): The style of the gradient.

            - ``"horizontal"``: Simple left-to-right gradient.
            - ``"vertical"``: Simple top-to-bottom gradient.
            - ``"linear"``: Gradient along a line from ``position[0]`` (tuple) to ``position[1]`` (tuple).
            - ``"radial"``: Radial gradient with centre ``position[0]`` (tuple) and radius ``position[1]`` (float).
            - ``"conical"``: Constant along the radius, varying with angle. ``position[0]`` (tuple) is the centre,
              ``position[1]`` (float) is the starting angle in degrees from the positive y-axis, defaulting to 0.
              For ``"linear"``, ``"radial"``, and ``"conical"``, ``position`` is determined automatically if not specified.

            Defaults to ``"horizontal"``.
        position (tuple): See ``style``.
        extend (str): How the gradient behaves outside the range specified in `position`. Can be ``"pad"``, ``"repeat"`` or
            ``"reflect"`` (only applies when style is ``"linear"`` or ``"radial"`` and `position` is specified). Defaults to ``"pad"``.
        resolution (int): The resolution of the gradient, when it is a matplotlib (or cmasher) cmap. Does not do
            anything when the cmap is a dict or a list. Defaults to ``256``.

    Returns:
        QGradient: A gradient object.
    """
    style = style.lower()
    extend = extend.lower()
    if style in ["horizontal", "vertical"]:
        if position is not None:
            raise ValueError(f"If gradient has style {style}, position must not be specified.")
        else:
            gradient = QLinearGradient()
            gradient.autoscale = True

    elif style == "linear":
        if position is None:
            raise ValueError(f"If gradient has style {style}, position must be specified.")
        else:
            gradient = QLinearGradient(QPointF(*position[0]), QPointF(*position[1]))
            gradient.autoscale = False
    elif style == "radial":
        if position is None:
            gradient = QRadialGradient()
            gradient.autoscale = True
        else:
            gradient = QRadialGradient(QPointF(*position[0]), position[1])
            gradient.autoscale = False
    elif style == "conical":
        if position is None:
            gradient = QConicalGradient()
            gradient.autoscale = True
        else:
            gradient = QConicalGradient(QPointF(*position[0]), position[1])
            gradient.autoscale = False
    else:
        raise ValueError('`style` must be "horizontal", "vertical", "linear", "radial" or "conical".')

    if extend == "pad":
        gradient.setSpread(QGradient.PadSpread)
    elif extend == "repeat":
        gradient.setSpread(QGradient.RepeatSpread)
    elif extend == "reflect":
        gradient.setSpread(QGradient.ReflectSpread)
    else:
        raise ValueError('`extend` must be "pad", "repeat" or "reflect".')

    gradient.cmap = cmap
    gradient.style = style
    gradient.resolution = resolution
    return gradient


def get_cmap(data: str | dict[float, ColorType] | Iterable[ColorType], source: str = "matplotlib"):
    """Tool for getting cmap from different sources.

    If ``data`` is of type ``str``, ``source`` decides from which library the cmap is obtained.

    Args:
        data (str, list of :ref:`Colortype` or dict of float to :ref:`Colortype`): Has different behaviour depending on type:

            - str: Name of the cmap. ``source`` specifies from which library the cmap is obtained.
            - dict: ``data[x]`` is the cmap color at ``x``, where the cmap is defined from ``x=0`` to ``x=1``. Every value not in
              ``data`` is interpolated. So e.g. ``data`` can be ``{0.0: "green", 0.25: "red", 1.0: "blue"}``, which would
              mean a cmap going from green to red rather quickly, and then slowly turning blue.
            - list: similar to ``dict``, but equally spaced colors in order.

        source (str): Library to obtain cmap from if it is a string. Currently, you can choose from matplotlib and
            colorcet. Feel free to request more.
    Returns:
        Callable: A function that interpolates to find the best approximation of the color at location ``i``: a value
        between ``0`` and ``1``.
    """
    if callable(data):  # probably catches too much, todo: check
        return data

    if isinstance(data, list):  # turns data into dict with equal spacing
        data = {index / (len(data) - 1): np.array(get_single_color(col).toTuple()) for index, col in enumerate(data)}

    if isinstance(data, str):
        def cmap_func(i):
            return colormap.get(data, source).map(i)

    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = np.array(get_single_color(value).toTuple())
        keys, values = map(np.array, zip(*sorted(data.items())))

        def cmap_func(i):
            """
            Interpolates to find the best approximation of the color at location `i`.
            A cmap generated from a dictionary defines color values at different positions on the interval [0, 1]. This
            function finds the closest two colors to `i`, and interpolates appropriately. If `i` is smaller than the
            lowest point at which a color is defined (usually 0), then this function returns the color at that lowest
            point, and similarly for the highest point.
            Works for scalar and array input.
            """
            i_arr = np.asarray(i)  # turns i into 1D array if it is just a number.
            is_scalar = i_arr.ndim == 0
            original_shape = i_arr.shape
            i_arr = i_arr.ravel()
            indices = np.array(np.searchsorted(keys, i_arr))  # index of first item that is bigger than i.

            lower_bound = indices == 0
            upper_bound = indices == max(keys)

            result = np.zeros((len(i_arr), 4))
            result[lower_bound] = values[0]
            result[upper_bound] = values[-1]

            interior = ~(lower_bound | upper_bound)

            if np.any(interior):
                interior_indices = indices[interior]
                interior_i = i_arr[interior]

                v_1, v_2 = values[interior_indices - 1], values[interior_indices]
                x_1, x_2 = keys[interior_indices - 1], keys[interior_indices]

                result[interior] = v_1 + (v_2 - v_1) * ((interior_i - x_1) / (x_2 - x_1))[:, np.newaxis]

            if is_scalar:
                return result[0]
            else:
                return result.reshape(original_shape + (4,))

            # Simplified slower version with iteration instead of array calculations below. Does not include dealing with bounds.
            # result = np.zeros((len(i), 4))
            # for ii, index in enumerate(indices):
            #     v_1, v_2, x_1, x_2 = values[index - 1], values[index], keys[index - 1], keys[index]
            #     result[ii] = v_1 + (v_2 - v_1) / (x_2 - x_1) * (i[ii] - x_1)
    else:
        raise TypeError("cmap is of incorrect type. Must be str, list or dict.")

    cmap_func.data = data

    return cmap_func


def cmap_to_gradient(cmap, gradient):
    """
    cmap must be from get_cmap, or accepted by get_cmap, and the gradient must be from get_gradient
    """
    cmap = get_cmap(cmap)
    if isinstance(cmap.data, str):
        for i in range(gradient.resolution):
            value = cmap(i / (gradient.resolution - 1))
            gradient.setColorAt(i / (gradient.resolution - 1), get_single_color(value))
    else:
        for key, value in cmap.data.items():
            gradient.setColorAt(key, get_single_color(value))
    return gradient


def cmap_to_colors(cmap, N_points):       # todo: temporary, make this better
    colors = np.zeros((N_points, 4))
    if isinstance(cmap, dict):
        col_arr = np.array(list(np.array(get_single_color(col).toTuple()) for col in cmap.values()))
        x_arr = np.linspace(0, 1, N_points)
        for i in range(4):
            colors[:, i] = np.interp(x_arr, list(cmap.keys()), col_arr[:, i])
    else:
        for i in range(N_points):
            colors[i] = cmap(i / (N_points - 1))

    return colors

