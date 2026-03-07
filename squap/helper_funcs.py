import ast
import os.path
import json
from typing import TypeAlias, Union, Iterable, Optional

import numpy as np
from PySide6.QtGui import QGradient, Qt, QColor, QPen

from PySide6.QtWidgets import QTableWidgetItem
from pyqtgraph import mkPen, mkColor


ColorType: TypeAlias = Union[QColor, mkColor, str, Iterable[float], float]
ColorsType: TypeAlias = Union[ColorType, Iterable["ColorsType"]]        # allows arbitrary nesting

# def map_color(color_name):
#     translator = str.maketrans({'_': '', ' ': ''})
#
#     color_name = color_name.translate(translator).lower()
#     col_dict = {
#         "w": "white", "r": "red", "g": "green", "b": "blue", "y": "yellow", "c": "cyan", "m": "magenta",
#         "darkgray": "darkGray", "lightgray": "lightGray", "darkred": "darkRed", "darkgreen": "darkGreen",
#         "darkblue": "darkBlue", "darkcyan": "darkCyan", "darkmagenta": "darkMagenta", "darkyellow": "darkYellow",
#     }
#
#     if color_name in col_dict:
#         color_name = col_dict[color_name]
#     return color_name


# def construct_color(color):   # accepts color name (see map_color), tuple of 3 or 4 ints between 0 and 255
#     # tuple of 3 or 4 floats between 0 and 1, or hex string starting with #
#     if isinstance(color, str):
#         color = map_color(color)
#         return QColor(color)
#     elif isinstance(color, tuple):
#         return QColor(*color)
#     # elif isinstance(color, list) or isinstance(color, np.ndarray):
#     #     colors = []
#     #     for col in color:
#     #         colors.append(construct_color(col))
#     #     return colors
#     elif isinstance(color, QColor):
#         return QColor(color)
#     else:
#         return QColor(color)
#         raise TypeError(
#         f"Not sure how to make a color from {color} with type {type(color)}. If this is a mistake send me a message"
#         )   # error #1007

def update_pen(pen: QPen, **kwargs) -> QPen:
    """Update existing pen `pen` using kwargs.

    Note that changing the pen won't affect plots that already exist. The pen needs to be reassigned.

    Args:
        pen (mkPen): Pen to update.
        **kwargs: Can contain the following:
            "color": new color or gradient
            "width" (int): new width
            "dashed" (bool): draw dashed
            "dash_pattern" (List[int]): list of integers representing dash, gap sizes consecutively. Can be any even
                length and the pattern is repeated.

    Returns:
        QPen: The changed pen (old pen has also been changed).
    """
    if "color" in kwargs:
        if kwargs["color"] is not None:
            if isinstance(kwargs["color"], QGradient):
                pen.setBrush(kwargs["color"])
            else:
                pen.setBrush(get_single_color(kwargs["color"]))

    if "width" in kwargs:
        if kwargs["width"] is not None:
            if kwargs["width"] < 0:
                return None
            pen.setWidth(kwargs["width"])


    if "dashed" in kwargs:
        if kwargs["dashed"]:
            pen.setStyle(Qt.PenStyle.DashLine)
            if "dash_pattern" not in kwargs:
                pen.setDashPattern([16, 16])        # not perfect. turning dash off and on will forget the old dashpattern
            if "dash_pattern" in kwargs:
                pen.setDashPattern(kwargs["dash_pattern"])
        else:
            pen.setStyle(Qt.PenStyle.SolidLine)

    else:
        if "dash_pattern" in kwargs:
            pen.setDashPattern(kwargs["dash_pattern"])

        # pen.stored_dash_pattern = None
    return pen


def qvect_to_arr(qvect):    # turns any type of QVector into an array
    return np.array(qvect.toTuple())


def textify(value):         # consistent value layout. If it is too large or small, it will be represented in e notation
    if 0.001 < value <= 1e5:
        text = str(round(value, 12))
    else:
        text = f"{value:.9e}"
    return text


def is_iter(arg):
    if hasattr(arg, "__iter__") and not isinstance(arg, str):
        return True
    else:
        return False


def is_multiple_colors(arg):
    if is_iter(arg):
        if is_iter(arg[0]):
            return True
        elif (len(arg) == 3 or len(arg) == 4) and (isinstance(arg[0], float) or isinstance(arg[0], int)):
            return False
        else:
            return True
    else:
        return False


def get_single_color(input_col):
    if is_iter(input_col):
        if isinstance(input_col[0], float) or isinstance(input_col[0], int):
            if len(input_col) == 3 or len(input_col) == 4:
                return mkColor(np.array(input_col)*255)
            else:
                raise ValueError(f"Expected tuple of lenght 3 or 4, but got length {len(input_col)} (Note that a "
                                 f"line can only be one color).")
        else:
            raise TypeError(f"When an iterable is provided, it should have elements that are floats. "
                            f"Got {type(input_col)} with elements {type(input_col[0])} (Note that colors are values between 0 and 1 not 0 and 255. Also note"
                            f" that a line can only be one color).")
    else:
        return mkColor(input_col)


def mkcol_to_arr(col):
    return np.array(col.toTuple())/255


def normalise_arr(arr):
    arr = np.array(arr)
    arr -= np.min(arr)
    arr /= np.max(arr)
    return arr


def get_type_func(value, parent, col):
    # this for-loop is essentially get_instance(value) and then assigns type_func
    if value is None:
        type_func = ast.literal_eval
        return type_func
    for instance in [int, str, float, complex, bool, list, dict, tuple, set, range, np.ndarray]:
        if isinstance(value, instance):  # checks a bunch of instances, and if it is one of them,
            if instance in [int, str, float, complex, bool, list, dict, tuple, set]:
                type_func = ast.literal_eval

            elif instance is range:
                type_func = lambda string: range(*(
                    int(i) for i in string.replace(" ", "").replace(")", "").split("(")[1].split(",")))

            elif instance is np.ndarray:
                parent.setItem(parent.current_row, col, QTableWidgetItem(
                    json.dumps(value.tolist())))
                type_func = lambda string: np.array(json.loads(string))
            else:
                raise AssertionError("This should never run.")

            return type_func
    else:
        raise NotImplementedError(
            "the instance you are using (the type of the variable provided) is currently not supported"
            "do you think it should be? send me an e-mail at rikmulder7@proton.me, and mention the "
            f"type was probably: {type(value)}")


def get_new_kwargs(current_locals, none_kwargs, exclude_args):
    """
    makes new kwargs exluding some kwargs and excluding some kwargs only if they are left at None.

    Args:
        current_locals: pass locals()
        none_kwargs: kwargs to skip if they are None
        exclude_args: kwargs to always exclude. Stuff like "self", "args", "kwargs"
    """
    new_kwargs = {}
    for k, v in current_locals.items():
        if k not in exclude_args and not (k in none_kwargs and v is None):
            new_kwargs[k] = v

    return new_kwargs


def transform_kwargs(kwargs, mapping):
    """Apply mapping to check kwargs for aliases."""
    result = {}
    for k, v in kwargs.items():
        if k not in result:
            result[mapping.get(k, k)] = v

    return result


def test_print(*args, **kwargs):
    print(f"filename={os.path.basename(__file__)}: ", end="")
    print(*args, **kwargs)
