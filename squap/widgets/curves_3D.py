from pyqtgraph.opengl import GLScatterPlotItem
import numpy as np
from typing import Optional, Iterable

from ..helper_funcs import is_multiple_colors, get_single_color, transform_kwargs

class ScatterCurve3D(GLScatterPlotItem):
    kwarg_mapping = {"c": "color", "colour": "color", "pixel_mode": "pxMode", "data": "pos", "s": "size"}

    def set_data(self, x: Optional[Iterable] = None, y: Optional[Iterable] = None, z: Optional[Iterable] = None,
                 **kwargs):
        """
        Sets the data of the scatter plot item after it has been created. Use either ``x``, ``y`` and ``z`` or ``pos`` to set the coordinates of the
        points.

        Args:
            x: New x-locations of each point. Defaults to ``None``, meaning the previous value of ``x``.
            y: New y-locations of each point. Defaults to ``None``, meaning the previous value of ``y``.
            z: New z-locations of each point. Defaults to ``None``, meaning the previous value of ``z``.

        Keyword Args:
            pos (:class:`np.ndarray <numpy.ndarray>`): Shape ``(N, 3)`` (:class:`array <numpy.ndarray>`) of floats
                specifying point locations. Can be used instead of ``x``, ``y`` and ``z``.
            color (:ref:`ColorsType`): Changes the color of the points. See :ref:`ColorsType`
                for allowed values.
            size (int or list of int): Array of floats specifying point size, or a single value to apply to all points.
            pixel_mode (bool): Whether to fix the size of each point. If ``True``, size is specified
                in pixels. If ``False``, size is specified in data coordinates. Defaults to ``True``.

        """
        new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)

        if "color" in new_kwargs:
            color = new_kwargs["color"]
            if is_multiple_colors(color):
                color = [get_single_color(col_i) for col_i in color]
            else:
                color = get_single_color(color)
            new_kwargs["color"] = color

        if x is None and y is None and z is None:
            self.setData(**new_kwargs)
        else:
            if x is None:
                x = self.pos[:, 0]
            if y is None:
                y = self.pos[:, 1]
            if z is None:
                z = self.pos[:, 2]
            pos = np.array((x, y, z)).T         # faster than columnstack
            self.setData(pos=pos, **new_kwargs)

