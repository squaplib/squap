from ..helper_funcs import textify, get_type_func, ColorType, get_single_color

import numpy as np
from typing import Any, Callable, Optional, Iterable
from time import time as current_time
import os.path

from pyqtgraph import ColorButton

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem,
    QLabel, QSlider, QCheckBox, QPushButton, QComboBox
)
from PySide6.QtCore import Qt


class Box:              # I am not sure if this is required, but I feel like it helps the IDE and is better organized
    """General class for each squap box.

    Args:
        parent (:class:`InputTable <squap.widgets.input_widget.InputTable>`): The parent :class:`InputTable <squap.widgets.input_widget.InputTable>`.

    Attributes:
        row (int): Row of the box. Is used when removing it after it has been created.
        textbox (:class:`QLabel <PySide6.QtWidgets.QLabel>`): The :class:`QLabel <PySide6.QtWidgets.QLabel>` object
            corresponding to this box.
    """

    def __init__(self, parent: 'InputTable'):    # parent will be the InputWidget
        self.parent = parent
        self.change_funcs = {}  # This is so that they can be reordered later if necessary
        # this is used when print_value is set to True during runtime, as it should still be the first function that is
        # called. So the printing function would be bound and then all other functions would be rebound.
        # It is a dictionary to allow unbinding functions, since the function passed `box.bind` is sometimes
        # different from the actual bound function

        self.row = None         # For removing it later (should be set inside the function)
        self.textbox = None     # So that you can check if a textbox exists for this box
        self.link_funcs = {}    # For linking this box to other boxes, change to `None` for unlinkable boxes
        # when linking, if multiple boxes have `printing_val` `True`, all but one are set to `False`
        self.printing_val = False

    def change_params(self, **kwargs):
        """
        Change box parameters. ``kwargs`` can usually be the same arguments that are given to the ``__init__`` function
        of this box, except ``init_value`` and ``row``.
        """
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def bind(self, func: Callable):
        """
        Bind function ``func`` to this box, meaning that when the value of the box is changed, the function is called.

        Args:
            func (:term:`callable`): function to bind to this box.
        """
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def unbind(self, func: Callable):
        """
        Unbind function. Is used internally when removing a box.

        Args:
            func (:term:`callable`): function to unbind from this box.
        """
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def _on_change(self, *args):        # Function that updates the var.var_name value upon value change
        """
        Update the associated variable when the user interacts with the box. Not really meant for users.
        """
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def value(self):
        """
        Return the current value of :ref:`var.var_name <squap.var>`
        """
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def set_value(self, value):
        """
        Set the value of the box and :ref:`var.var_name <squap.var>` to ``value``. Note that for a slider, the new slider position will be
        the closest possible position to ``value``, and the new value of :ref:`var.var_name <squap.var>` will be the value corresponding to
        the new slider position.
        """
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def print_val(self):
        """
        Print the current value of the box. Used for the ``print_value`` keyword argument.
        """
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def remove(self):
        """
        Remove this box.
        """
        # if self.textbox is not None:
        #     self.textbox.destroy()          # not sure if this does anything
        self.parent.remove_row(self.row, self)


class InputTable(QTableWidget):    # table for all inputs
    def __init__(self, width: int, height: int, name: str, window):    # takes window as an argument so that it can inherit
        # update_funcs and variables easily
        super().__init__()

        self.name = name
        self.resize(width, height)

        self.setRowCount(0)
        self.setColumnCount(3)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.col_partition = 1/3                # where is the partition between col 0 & col 1, should be between 0&1
        self.rate_slider_space = 60             # pixels of space a rate_slider gets

        self.setColumnWidth(0, int(width * self.col_partition))
        self.setColumnWidth(1, int(self.rate_slider_space))
        self.setColumnWidth(2, int(width * (1-self.col_partition))-self.rate_slider_space)

        # this cell is split in 2 for the rate_slider

        self.current_row = -1       # row of the last placed widget (so total amount of rows - 1)
        self.variables = window.variables
        self.window = window        # necessary for renaming tabs
        self.input_varnames = []    # the names of every variable indexed by row for stuff like linking and rate_slider
        self.boxes = []             # for removing them later (and a nice overview)
        self.empty_rows = []      # these are the rows that have been removed out of order, so that these are filled
                                    # up first

    def resizeEvent(self, *args) -> None:       # event is not used since every necessary parameter is in self
        width = self.width()
        height = self.height()

        self.setGeometry(0, 0, width, height)

        if self.rowHeight(0)*(self.current_row+1)+26 <= height:
            width -= 2
        else:
            width -= 18

        self.setColumnWidth(0, int(width * self.col_partition))
        self.setColumnWidth(1, int(self.rate_slider_space))
        self.setColumnWidth(2, int(width * (1-self.col_partition))-self.rate_slider_space)

    def rename(self, name: str):
        """Renames the table. The name is only visible when multiple tabs are present."""
        self.window.table_manager.rename_tab(name, old_name=self.name)

    def set_partition(self, fraction=1/3):
        """
        Sets the position of the partition between the 2 columns of the :class:`~squap.widgets.input_widget.InputTable`.

        Args:
            fraction (float): float between ``0`` and ``1``, specifying the portion of the window taken up by the partition.
                Starts off as ``1/3``.
        """
        self.col_partition = fraction
        self.resizeEvent()

    def get_boxes(self) -> list[Box]:        # assumes actual widget is the leftmost widget
        """
        Returns a list containing all :class:`boxes <squap.widgets.Box>` that exist at this point.

        Returns:
            list of Box: list of all :class:`boxes <squap.widgets.Box>` added in order.
        """
        return [box_row[-1] for box_row in self.boxes]

    def add_widget(self, row: None | int, box_row: tuple[Box, ...]) -> int:     # if row is specified and row is in empty_rows it is added there
        """
        Handles all internal stuff that is required when a :class:`box <squap.widgets.Box>` is added to a
        specified row. The row can be the next row or any empty row.
        Args:
            row (None or int): Row in which to add the box. Pass ``None`` to add it to a next row, or choose a row that has
                no :class:`boxes <squap.widgets.Box>` in it yet.
            box_row (tuple of Box): `tuple` containing all :class:`boxes <squap.widgets.Box>` in the row
                (so usually a :class:`textbox <PySide6.QtWidgets.QLabel>` and :class:`box widget <squap.widgets.Box>`)

        Returns:
            int: Row in which the :class:`box <squap.widgets.Box>` has been added.
        """
        if row is None or row == self.current_row+1:
            if not self.empty_rows:
                self.current_row += 1
                self.setRowCount(self.current_row + 1)
                table_height = self.rowHeight(0)*(self.current_row+1)+26
                if table_height >= self.height():
                    self.resizeEvent(None)

                self.boxes.append(box_row)
                return self.current_row
            else:
                self.empty_rows.sort()
                new_row = self.empty_rows[0]
                self.empty_rows.remove(new_row)

                self.boxes[new_row] = box_row
                return new_row
        elif row in self.empty_rows:
            self.empty_rows.remove(row)
            self.boxes[row] = box_row
            return row
        elif row > self.current_row + 1:
            extra_rows = []
            for _ in range(row - self.current_row):
                self.current_row += 1
                self.setRowCount(self.current_row + 1)
                table_height = self.rowHeight(0) * (self.current_row + 1) + 26
                if table_height >= self.height():
                    self.resizeEvent(None)
                extra_rows.append(self.current_row)
            self.boxes.extend([()]*(len(extra_rows)-1))
            self.empty_rows.extend(extra_rows[:-1])
            self.boxes.append(box_row)
            return self.current_row
        else:
            raise ValueError(f"row {row} is not empty")

    def remove_row(self, remove_row: int, remove_box: Box):
        """
        Remove box ``remove_box`` from row ``remove_row``.

        Args:
            remove_row (int): row from which to remove the :class:`box <squap.widgets.Box>`.
            remove_box (Box): :class:`Box <squap.widgets.Box>` to remove.
        """
        if remove_row in self.empty_rows or remove_row > self.current_row:
            raise ValueError(f"row {remove_row} is already empty.")
        for func in remove_box.change_funcs:
            remove_box.unbind(func)

        if not isinstance(remove_box, self.Button):
            remove_box.unbind(remove_box._on_change)

        for col, box in enumerate(self.boxes[remove_row]):
            if isinstance(box, self.InputBox) or isinstance(box, self.RateSlider):
                self.setItem(remove_row, col, QTableWidgetItem(""))
            else:
                self.setCellWidget(remove_row, col, None)

        if remove_row == self.current_row:
            self.current_row -= 1
            self.setRowCount(self.current_row + 1)
            self.boxes.pop(-1)
        else:
            self.setSpan(remove_row, 0, 1, 1)
            self.setSpan(remove_row, 1, 1, 1)
            self.setSpan(remove_row, 2, 1, 1)
            for col in range(3):
                item = self.item(remove_row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make uneditable

            self.empty_rows.append(remove_row)
            self.boxes[remove_row] = ()

    def add_slider(self, name: str, init_value: float = 1.0, min_value: float = 0.0, max_value: float = 10.0,
                   n_ticks: int = 51, tick_interval: Optional[float] = None, only_ints: bool = False,
                   logscale: bool = False, custom_arr: Optional[Iterable] = None, var_name: Optional[str] = None,
                   print_value: bool = False, row: Optional[int] = None) -> 'InputTable.Slider':
        """Creates a :class:`slider <squap.widgets.InputTable.Slider>` with the given parameters, and adds it to this
        :class:`input table <squap.widgets.input_widget.InputTable>`. See :func:`squap.add_slider`
        for initialisation information.

        Returns:
            InputTable.Slider: The created :class:`slider widget <squap.widgets.InputTable.Slider>`.
        """
        return self.Slider(self, name, init_value, min_value, max_value, n_ticks, tick_interval, only_ints, logscale,
                           custom_arr, var_name, print_value, row)

    def add_checkbox(self, name: str, init_value: bool = False, var_name: Optional[str] = None,
                     print_value: bool = False, row: Optional[int] = None) -> 'InputTable.CheckBox':
        """Creates a :class:`checkbox <squap.widgets.InputTable.CheckBox>` with the given parameters, and adds it to this
        :class:`input table <squap.widgets.input_widget.InputTable>`. See :func:`squap.add_checkbox`
        for initialisation information.

        Returns:
            InputTable.CheckBox: The created :class:`checkbox widget <squap.widgets.InputTable.CheckBox>`.
        """
        return self.CheckBox(self, name, init_value, var_name, print_value, row)

    def add_inputbox(self, name: str, init_value: Any = 1.0, type_func: Optional[Callable] = None,
                     var_name: Optional[str] = None, print_value: bool = False,
                     row: Optional[int] = None) -> 'InputTable.InputBox':
        """Creates an :class:`inputbox <squap.widgets.InputTable.InputBox>` with the given parameters, and adds it to
        this :class:`input table <squap.widgets.input_widget.InputTable>`. See :func:`squap.add_inputbox`
        for initialisation information.

        Returns:
            InputTable.InputBox: The created :class:`inputbox widget <squap.widgets.InputTable.InputBox>`.
        """
        return self.InputBox(self, name, init_value, type_func, var_name, print_value, row)

    def add_displaybox(self, name: str, var_name: Optional[str] = None,
                       print_value: bool = False, row: Optional[int] = None) -> 'InputTable.DisplayBox':
        """Creates an :class:`inputbox <squap.widgets.InputTable.DisplayBox>` with the given parameters, and adds it to
        this :class:`input table <squap.widgets.input_widget.InputTable>`. See :func:`squap.add_displaybox`
        for initialisation information.

        Returns:
            InputTable.DisplayBox: The created :class:`inputbox widget <squap.widgets.InputTable.DisplayBox>`.
        """
        return self.DisplayBox(self, name, var_name, print_value, row)

    def add_button(self, name: str, func: Optional[Callable] = None, row: Optional[int] = None) -> 'InputTable.Button':
        """Creates a :class:`button <squap.widgets.InputTable.Button>` with name ``name`` and bound function ``func``,
        and adds it to this :class:`input table <squap.widgets.input_widget.InputTable>`. See :func:`squap.add_button`
        for initialisation information.

        Returns:
            InputTable.Button: The created :class:`button widget <squap.widgets.InputTable.Button>`.
        """
        return self.Button(self, name, func, row)

    def add_dropdown(self, name: str, options: list, init_index: int = 0, option_names: Optional[Iterable[str]] = None,
                     var_name: Optional[str] = None, print_value: bool = False, row: Optional[int] = None) -> 'InputTable.Dropdown':
        """Creates a :class:`dropdown <squap.widgets.InputTable.Dropdown>` widget with the given parameters, and adds
        it to this :class:`input table <squap.widgets.input_widget.InputTable>`. See :func:`squap.add_dropdown` for
        initialisation information.

        Returns:
            InputTable.Dropdown: The created :class:`dropwdown widget <squap.widgets.InputTable.Dropdown>`."""
        return self.Dropdown(self, name, options, init_index, option_names, var_name, print_value, row)

    def add_rate_slider(self, name: str, init_value: float = 1.0, change_rate: float = 10.0, absolute: bool = False,
                        time_var: Optional[str] = None, custom_func: Optional[Callable] = None,
                        var_name: Optional[str] = None, print_value: bool = False,
                        row: Optional[int] = None) -> 'InputTable.RateSlider':
        """Creates a :class:`RateSlider <squap.widgets.InputTable.RateSlider>` with the given parameters, and adds it
        to this :class:`input table <squap.widgets.input_widget.InputTable>`. See :func:`squap.add_rate_slider` for
        initialisation information.

        Returns:
            InputTable.RateSlider: The created :class:`rate_slider widget <squap.widgets.InputTable.RateSlider>`.
        """
        return self.RateSlider(
            self, name, init_value, change_rate,
            absolute, time_var, custom_func, var_name, print_value, row
        )

    def add_color_picker(self, name: str, init_value: ColorType = (255, 255, 255), var_name: Optional[str] = None,
                         print_value: bool = False, row: Optional[int] = None) -> 'InputTable.ColorPicker':
        """Creates a :class:`ColorPicker <squap.widgets.InputTable.ColorPicker>` with the gives parameters, and adds it
        to this :class:`input table <squap.widgets.input_widget.InputTable>`. See :func:`squap.add_color_picker` for
        initialisation information.

        Returns:
            InputTable.ColorPicker: The created :class:`color_picker widget <squap.widgets.InputTable.ColorPicker>`.
        """
        return self.ColorPicker(
            self, name, init_value, var_name, print_value, row
        )

    class Slider(Box, QSlider):
        """
        Class for the slider widget. See :func:`squap.add_slider` for initialisation information.
        """
        def __init__(self, parent: 'InputTable', name: str, init_value: float, min_value: float, max_value: float,
                     n_ticks: int = 51, tick_interval: Optional[float] = None, only_ints: bool = False,
                     logscale: bool = False, custom_arr: Optional[Iterable] = None, var_name: Optional[str] = None,
                     print_value: bool = False, row: Optional[int] = None):
            Box.__init__(self, parent)
            QSlider.__init__(self, parent=parent, orientation=Qt.Orientation.Horizontal)

            (self.min_value, self.max_value, self.var_name, self.only_ints, self.logscale, self.custom_arr,
             self.n_ticks, self.tick_interval) = (min_value, max_value, var_name, only_ints, logscale, custom_arr,
                                                  n_ticks, tick_interval)
            # this bit is the same for most widgets:
            # <editor-fold desc="add_widget and init name&var_name">
            if name == "":          # if self.textbox will be created
                box_row = (self, )
            else:
                box_row = (self.textbox, self)
            row = parent.add_widget(row=row, box_row=box_row)
            self.row = row

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                col = 0
                parent.setSpan(row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                col = 1
                parent.setSpan(row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            parent.setCellWidget(row, col, self)
            # </editor-fold>

            self.setMinimum(0)

            self.current_name = var_name

            if custom_arr is not None:
                self.arr = custom_arr
            elif logscale:
                if min_value*max_value <= 0:
                    raise ValueError("`min_value` and `max_value` must have the same sign when `logscale` is enabled.")
                if not tick_interval:
                    self.arr = np.logspace(np.log10(min_value), np.log10(max_value), int(n_ticks))
                else:
                    n_ticks = round(np.emath.logn(tick_interval, max_value/min_value))
                    self.arr = np.logspace(np.log10(min_value), np.log10(max_value), n_ticks)
                if only_ints:
                    self.arr = np.round(self.arr).astype(int)
            elif only_ints:
                if tick_interval is None:
                    tick_interval = 1
                else:
                    tick_interval = int(tick_interval)
                # max_value = max_value - (max_value - min_value) % tick_interval
                self.arr = np.arange(min_value, max_value+tick_interval, tick_interval)
                # n = int((max_value - min_value) / tick_interval)
            else:
                if not tick_interval:
                    self.arr = np.linspace(min_value, max_value, int(n_ticks))
                else:
                    self.arr = np.arange(min_value, max_value+tick_interval, tick_interval)

            # slider.setStyleSheet("QSlider {height: 20px; width: 200px;}")     # makes sliders nicer
            n = len(self.arr)-1
            self.setMaximum(n)
            self.setSingleStep(1)  # increment between values
            self.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.setTickInterval(1)  # distance between ticks
            if n > 50:      # remove ticks after n=50 to not make it too cluttered
                self.setTickPosition(QSlider.NoTicks)
            else:
                self.setTickPosition(QSlider.TickPosition.TicksBelow)

            self.valueChanged.connect(self._on_change)       # connected before `set_value` because it needs to be
            # reconnected in this function
            self.set_value(init_value)

            if print_value:
                self.valueChanged.connect(self.print_val)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the slider. Only keyword arguments are accepted, and takes all arguments that
            :func:`squap.add_slider` accepts, except ``init_value`` and ``row``.
            """
            turn_on_print_func = False
            update_arr = False                  # if any parameters are changed such that self.arr changes
            arr_kwargs = ["min_value", "max_value", "n_ticks", "tick_interval", "only_ints", "logscale", "custom_arr"]

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
                self._on_change(self.value())   # when var_name or name changes, call self._on_change to update var.name
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]
                self._on_change(self.value())

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.valueChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True

            if "n_ticks" in kwargs and "tick_interval" not in kwargs:
                self.tick_interval = None

            for kwarg in arr_kwargs:
                if kwarg in kwargs:
                    update_arr = True
                    setattr(self, kwarg, kwargs[kwarg])

            if update_arr:
                old_arr = self.arr.copy()
                if "custom_arr" not in kwargs:      # if custom_arr is not provided but other arguments that change self.arr are
                    self.custom_arr = None

                if self.custom_arr is not None:
                    self.arr = self.custom_arr
                elif self.logscale:
                    if self.min_value * self.max_value <= 0:
                        raise ValueError("min_value and max_value must have the same sign when logscale is enabled.")
                    if not self.tick_interval:
                        self.arr = np.logspace(np.log10(self.min_value), np.log10(self.max_value), self.n_ticks)
                    else:
                        n_ticks = round(np.emath.logn(self.tick_interval, self.max_value / self.min_value))
                        self.arr = np.logspace(np.log10(self.min_value), np.log10(self.max_value), n_ticks)
                elif self.only_ints:
                    if self.tick_interval is None:
                        tick_interval = 1
                    else:
                        tick_interval = int(self.tick_interval)

                    self.arr = np.arange(self.min_value, self.max_value + tick_interval, tick_interval)
                    # self.max_value = self.max_value - (self.max_value-self.min_value) % tick_interval
                    # n = int((self.max_value-self.min_value)/tick_interval)
                else:
                    # print(not float(self.tick_i?nterval))
                    if self.tick_interval is None:
                        if "n_ticks" in kwargs.keys():
                            n_ticks = int(kwargs["n_ticks"])
                        else:
                            n_ticks = len(self.arr)
                        self.arr = np.linspace(self.min_value, self.max_value, n_ticks)
                    else:
                        self.arr = np.arange(self.min_value, self.max_value+self.tick_interval, self.tick_interval)

                if len(self.arr) == 0:
                    self.arr = old_arr
                    raise ValueError("Current parameters give an empty array")

                n = len(self.arr) - 1
                self.setMaximum(n)
                if n > 50:
                    self.setTickPosition(QSlider.NoTicks)
                else:
                    self.setTickPosition(QSlider.TickPosition.TicksBelow)

                current_val = getattr(self.parent.variables, self.current_name)
                if self.logscale:
                    slider_val = np.argmin(np.abs(np.log10(np.array(self.arr)) - np.log10(current_val)))
                else:
                    slider_val = np.argmin(np.abs(np.array(self.arr) - current_val))

                self.setValue(slider_val)       # also automatically calls _on_change

            if turn_on_print_func:
                self.valueChanged.connect(self.print_val)
                self.printing_val = True

                for func in self.change_funcs.values():      # reorders change_funcs so that print_val is first
                    self.valueChanged.disconnect(func)
                    self.valueChanged.connect(func)

        def bind(self, func):
            # makes sure function is called without argument (removing this breaks examples/all_plot_options.py
            def new_func():
                func()

            self.change_funcs[func] = new_func
            self.valueChanged.connect(new_func)
            return self

        def unbind(self, func):
            if func not in self.change_funcs and func != self._on_change:
                raise ValueError("Function is not bound to this Box.")
            if func != self._on_change:
                self.valueChanged.disconnect(self.change_funcs[func])
                self.change_funcs.pop(func)
            else:
                self.valueChanged.disconnect(self._on_change)

            return self

        def _on_change(self, val):
            setattr(self.parent.variables, self.current_name, self.arr[val])

        def set_value(self, value):
            if self.logscale:
                slider_val = np.argmin(np.abs(np.log10(np.array(self.arr)) - np.log10(value)))
            else:
                slider_val = np.argmin(np.abs(np.array(self.arr) - value))
            setattr(self.parent.variables, self.current_name, value)
            self.valueChanged.disconnect(self._on_change)        # so that `var.current_name` is set to `value` not
            # the closest possible value in `self.arr`.
            self.setValue(slider_val)
            self.valueChanged.connect(self._on_change)

        def value(self):
            return getattr(self.parent.variables, self.current_name)

        def set_index(self, index):
            """Sets the index to ``index``."""
            self.setValue(index)

        def index(self):
            """Returns the current index."""
            return super(QSlider, self).value()     # self.value is overwritten so we want to access the parent one.

        def print_val(self):
            print(f"{self.current_name} = {self.value()}")

    class CheckBox(Box, QCheckBox):
        """
        Class for the checkbox widget. See :func:`squap.add_checkbox` for initialisation information.
        """
        def __init__(self, parent: 'InputTable', name: str, init_value: bool, var_name: Optional[str] = None,
                     print_value: bool = False, row: Optional[int] = None):
            Box.__init__(self, parent)
            QCheckBox.__init__(self)

            self.var_name = var_name

            # <editor-fold desc="add_widget and init name&var_name">
            if name == "":          # if self.textbox will be created
                box_row = (self, )
            else:
                box_row = (self.textbox, self)
            row = parent.add_widget(row=row, box_row=box_row)
            self.row = row

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                col = 0
                parent.setSpan(row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                col = 1
                parent.setSpan(row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            parent.setCellWidget(row, col, self)
            # </editor-fold>
            self.current_name = var_name

            setattr(parent.variables, self.current_name, init_value)

            self.setChecked(init_value)
            self.stateChanged.connect(self._on_change)

            if print_value:
                self.stateChanged.connect(self.print_val)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the checkbox. Only keyword arguments are accepted, and takes all arguments that
            :func:`squap.add_checkbox` accepts, except ``init_value`` and ``row``.
            """
            turn_on_print_func = False

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
                self._on_change()
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]
                self._on_change()

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.stateChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True

            if turn_on_print_func:
                self.stateChanged.connect(self.print_val)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.stateChanged.disconnect(func)
                    self.stateChanged.connect(func)

        def _val(self):  # turns checkbox state into tf value    (val because value is already used by some boxes)
            if self.checkState() == Qt.CheckState.Checked:
                return True
            else:
                return False

        def bind(self, func):
            # makes sure function is called without argument (removing this breaks examples/all_plot_options.py
            def new_func():
                func()

            self.change_funcs[func] = new_func
            self.stateChanged.connect(new_func)
            return self

        def unbind(self, func):
            if func not in self.change_funcs and func != self._on_change:
                raise ValueError("Function is not bound to this Box.")
            if func != self._on_change:
                self.stateChanged.disconnect(self.change_funcs[func])
                self.change_funcs.pop(func)
            else:
                self.stateChanged.disconnect(self._on_change)

            return self

        def _on_change(self):
            setattr(self.parent.variables, self.current_name, self._val())

        def set_value(self, value: bool):
            self.setChecked(value)

        def value(self):
            return getattr(self.parent.variables, self.current_name)

        def print_val(self):
            print(f"{self.current_name} = {self.value()}")

    class InputBox(Box):
        """
        Class for the inputbox widget. See :func:`squap.add_inputbox` for initialisation information.
        """
        def __init__(self, parent: 'InputTable', name: str, init_value: Any, type_func: Optional[Callable] = None,
                     var_name: Optional[str] = None, print_value: bool = False, row: Optional[int] = None):
            Box.__init__(self, parent)
            self.var_name = var_name

            # <editor-fold desc="add_widget and init name&var_name">
            if name == "":
                box_row = (self,)
            else:
                box_row = (self.textbox, self)
            row = parent.add_widget(row=row, box_row=box_row)
            self.row = row

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                self.col = 0
                parent.setSpan(row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                self.col = 1
                parent.setSpan(row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            # </editor-fold>

            if isinstance(init_value, str):
                parent.setItem(row, self.col, QTableWidgetItem('"' + init_value + '"'))
            else:
                parent.setItem(row, self.col, QTableWidgetItem(str(init_value)))

            self.current_name = var_name

            if type_func is None:
                self.type_func = get_type_func(init_value, parent, self.col)
            else:
                self.type_func = type_func

            setattr(parent.variables, self.current_name, init_value)
            self.parent.cellChanged.connect(self._on_change)

            if print_value:
                def print_func(row):
                    if row == self.row:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the inputbox. Only keyword arguments are accepted, and takes all arguments that
            :func:`squap.add_inputbox` accepts, except ``init_value`` and ``row``.
            """
            turn_on_print_func = False

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
                self._on_change(self.row)
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]
                self._on_change(self.row)

            if "type_func" in kwargs:
                if kwargs["type_func"] is None:
                    self.type_func = get_type_func(self.value(), self.parent, self.col)
                else:
                    self.type_func = kwargs["type_func"]

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.parent.cellChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True
            if turn_on_print_func:
                def print_func(row):
                    if row == self.row:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.parent.cellChanged.disconnect(func)
                    self.parent.cellChanged.connect(func)

        def bind(self, func):
            def new_func(row):
                if row == self.row:
                    func()

            self.change_funcs[func] = new_func
            self.parent.cellChanged.connect(new_func)
            return self

        def unbind(self, func):
            if func not in self.change_funcs and func != self._on_change:
                raise ValueError("Function is not bound to this Box.")

            if func != self._on_change:
                self.parent.cellChanged.disconnect(self.change_funcs[func])
                self.change_funcs.pop(func)
            else:
                self.parent.cellChanged.disconnect(self._on_change)

            return self

        def _on_change(self, row):
            if row == self.row:
                setattr(self.parent.variables, self.current_name, self.type_func(self.parent.item(self.row, self.col).text()))

        def value(self):
            return getattr(self.parent.variables, self.current_name)

        def set_value(self, value):
            if isinstance(value, str):
                self.parent.setItem(self.row, self.col, QTableWidgetItem('"' + value + '"'))
            else:
                self.parent.setItem(self.row, self.col, QTableWidgetItem(str(value)))

        def print_val(self):
            print(f"{self.current_name} = {self.value()}")

        def refresh_type_func(self, value: Any):         # Extra function for when type_func must be changed during runtime,
            """Updates the type function so that ``value`` would parse successfully."""
            self.type_func = get_type_func(value, self.parent, self.col)        # is not explained anywhere
            return self

    class DisplayBox(Box):
        def __init__(self, parent: 'InputTable', name: str, var_name: Optional[str] = None,
                     print_value: bool = False, row: Optional[int] = None):
            Box.__init__(self, parent)
            self.var_name = var_name

            # <editor-fold desc="add_widget and init name&var_name">
            if name == "":
                box_row = (self,)
            else:
                box_row = (self.textbox, self)
            row = parent.add_widget(row=row, box_row=box_row)
            self.row = row

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                self.col = 0
                parent.setSpan(row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                self.col = 1
                parent.setSpan(row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            # </editor-fold>

            self.current_name = var_name

            if self.current_name not in self.parent.variables._variables:       # fix?
                setattr(parent.variables, self.current_name, 0)

            parent.variables.on_change(self.current_name,
                                       lambda: self.set_value(getattr(self.parent.variables, self.current_name)))

            if print_value:
                def print_func(row):
                    if row == self.row:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the displaybox. Only keyword arguments are accepted, and takes all arguments that
            :func:`squap.add_displaybox` accepts, except ``row``.
            """
            turn_on_print_func = False

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
                self._on_change(self.row)
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]
                self._on_change(self.row)

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.parent.cellChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True
            if turn_on_print_func:
                def print_func(row):
                    if row == self.row:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.parent.cellChanged.disconnect(func)
                    self.parent.cellChanged.connect(func)

        def set_value(self, value):
            if isinstance(value, str):
                self.parent.setItem(self.row, self.col, QTableWidgetItem('"' + value + '"'))
            else:
                self.parent.setItem(self.row, self.col, QTableWidgetItem(str(value)))

        def print_val(self):
            print(f"{self.current_name} = {self.value()}")


    class Button(Box, QPushButton):
        """
        Class for the button widget. See :func:`squap.add_button` for initialisation information.
        """
        def __init__(self, parent: 'InputTable', name: str, func: Optional[Callable] = None, row: Optional[int] = None):
            Box.__init__(self, parent)
            QPushButton.__init__(self, parent=parent, text=name)
            self.link_funcs = None

            row = parent.add_widget(row=row, box_row=(self, ))
            self.row = row

            parent.setSpan(row, 0, 1, 3)
            parent.input_varnames.append(None)        # so that indexing still works
            parent.setCellWidget(row, 0, self)

            if func is not None:
                self.bind(func)         # is a user provided function, so now we can use bind
                self.main_func = func
            else:
                self.main_func = None

        def change_params(self, **kwargs):
            """
            Changes the parameters of the button. Accepts ``name`` and ``func`` as keyword arguments.
            """

            if "name" in kwargs:
                self.setText(kwargs["name"])
            if "func" in kwargs:
                self.unbind(self.main_func)
                self.main_func = kwargs["func"]
                self.bind(self.main_func)

        def bind(self, func):
            self.change_funcs[func] = func  # dict is not really necessary for button, but for consistency this is ok.
            self.clicked.connect(func)
            return self

        def unbind(self, func):
            if func not in self.change_funcs:
                raise ValueError("Function is not bound to this Box.")
            self.clicked.disconnect(func)
            self.change_funcs.pop(func)
            return self

        def _on_change(self):
            raise ValueError("This function is not defined for a Button")

        def set_value(self, value):
            raise ValueError("This function is not defined for a Button")

        def print_val(self):
            raise ValueError("This function is not defined for a Button")

    class Dropdown(Box, QComboBox):
        """
        Class for the dropwdown widget. See :func:`squap.add_dropdown` for initialisation information.
        """
        def __init__(self, parent: 'InputTable', name: str, options: list, init_index: int = 0,
                     option_names: Optional[Iterable[str]] = None, var_name: Optional[str] = None,
                     print_value: bool = False, row: Optional[int] = None):
            Box.__init__(self, parent)
            QComboBox.__init__(self)

            self.var_name, self.options, self.option_names = var_name, options, option_names
            if option_names is None:        # for change_params we need the original value, for this function not.
                for option in options:
                    if not isinstance(option, str):
                        option_names = [str(option) for option in options]
                        break
                else:
                    option_names = options

            # <editor-fold desc="add_widget and init name&var_name">
            if name == "":          # if self.textbox will be created
                box_row = (self,)
            else:
                box_row = (self.textbox, self)
            row = parent.add_widget(row=row, box_row=box_row)
            self.row = row

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                col = 0
                parent.setSpan(row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                col = 1
                parent.setSpan(row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            parent.setCellWidget(row, col, self)
            # </editor-fold>
            self.current_name = var_name

            self.addItems(option_names)
            self.setCurrentIndex(init_index)

            setattr(parent.variables, self.current_name, options[init_index])

            self.currentTextChanged.connect(self._on_change)

            if print_value:
                self.currentTextChanged.connect(self.print_val)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the dropdown. Only keyword arguments are accepted, and takes all arguments that
            :func:`squap.add_dropdown` accepts, except ``init_value`` and ``row``.
            """
            turn_on_print_func = False
            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
                self._on_change()
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]
                self._on_change()

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.currentTextChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True

            if "option_names" in kwargs:
                self.option_names = kwargs["option_names"]
                for _ in range(len(self.options)):
                    self.removeItem(0)
                self.addItems(self.option_names)

            if "options" in kwargs:
                if self.option_names is None:
                    for _ in range(len(self.options)):
                        self.removeItem(0)
                    for option in kwargs["options"]:
                        if not isinstance(option, str):
                            option_names = [str(option) for option in kwargs["options"]]
                            break
                    else:
                        option_names = kwargs["options"]
                    self.addItems(option_names)
                self.options = kwargs["options"]

            if turn_on_print_func:
                self.currentTextChanged.connect(self.print_val)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.currentTextChanged.disconnect(func)
                    self.currentTextChanged.connect(func)

        def bind(self, func):
            # makes sure function is called without argument (removing this breaks examples/all_plot_options.py
            def new_func():
                func()

            self.change_funcs[func] = new_func
            self.currentTextChanged.connect(new_func)
            return self

        def unbind(self, func):
            if func not in self.change_funcs and func != self._on_change:
                raise ValueError("Function is not bound to this Box.")
            if func != self._on_change:
                self.currentTextChanged.disconnect(self.change_funcs[func])
                self.change_funcs.pop(func)
            else:
                self.currentTextChanged.disconnect(self._on_change)
            return self

        def _on_change(self):
            setattr(self.parent.variables, self.current_name, self.options[self.currentIndex()])

        def value(self):
            return getattr(self.parent.variables, self.current_name)

        def set_value(self, value):
            if self.option_names is None:        # for change_params we need the original value, for this function not.
                option_names = self.option_names
            else:
                option_names = self.options
            self.setCurrentIndex(option_names.index(value))

        def set_index(self, index):
            """Sets the index to ``index``."""
            self.setCurrentIndex(index)

        def index(self):
            """Returns the current index."""
            return self.currentIndex()

        def print_val(self):
            print(f"{self.current_name} = {self.options[self.currentIndex()]}")

    class RateSlider(Box, QSlider):
        """
        Class for the rate_slider widget. See :func:`squap.add_rate_slider` for initialisation information.
        """
        def __init__(self, parent: 'InputTable', name: str, init_value: float, change_rate: float = 10.0,
                     absolute: bool = False, time_var: Optional[str] = None, custom_func: Optional[Callable] = None,
                     var_name: Optional[str] = None, print_value: bool = False, row: Optional[int] = None):
            Box.__init__(self, parent)
            QSlider.__init__(self)
            self.slider = QSlider(Qt.Orientation.Horizontal, parent)    # done here so it can be added to parent.boxes
            self.actual_change_funcs = []       # for being able to unbind functions

            (self.var_name, self.change_rate, self.absolute, self.time_var,
             self.custom_func) = var_name, change_rate, absolute, time_var, custom_func
            # this bit is a bit different for the rate_slider \/\/
            # <editor-fold desc="add_widget and init name&var_name">
            if name == "":          # if self.textbox will be created
                box_row = (self.slider, self)
            else:
                box_row = (self.textbox, self.slider, self)
            row = parent.add_widget(row=row, box_row=box_row)
            self.row = row

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                rate_slider_col = 0
                self.col = 1
                parent.setSpan(row, 0, 1, 2)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                rate_slider_col = 1
                self.col = 2
                self.textbox = QLabel(name)
                parent.setCellWidget(row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            # </editor-fold>

            self.current_name = var_name

            setattr(parent.variables, self.current_name, init_value)

            parent.setCellWidget(self.row, rate_slider_col, self.slider)
            self.slider.setRange(0, 200)
            self.slider.setValue(100)
            self.slider.setStyleSheet("""
                    QSlider::groove:horizontal {
                        border: 1px solid #aaa;
                        width: 50px;
                        height: 8px;
                        border-radius: 4px;
                    }

                    QSlider::handle:horizontal {
                        background: #000;
                        border: 1px solid #000;
                        width: 14px;
                        height: 16px;
                        border-radius: 8px;
                        margin: -4px 0;
                    }
                """)
            self.slider.in_middle = True        # if the rate_slider is set to the middle, nothing needs to happen
            # so if this is set to False, it doesn't run the stuff, so when the rate_slider is released, the impact on
            # performance is minimal

            def release_func():  # resets rate_slider to 0 when released
                self.slider.setValue(100)
                self.slider.in_middle = True

            def press_func():
                self.timer = get_t()
                self.slider.in_middle = False

            self.slider.sliderReleased.connect(release_func)
            self.slider.sliderPressed.connect(press_func)

            parent.setItem(self.row, self.col, QTableWidgetItem(str(textify(init_value))))
            setattr(parent.variables, self.current_name, init_value)
            self.parent.cellChanged.connect(self._on_change)

            # <editor-fold desc="create rate_slider update func">
            if time_var is None:
                self.timer = current_time()
                
                def get_t():
                    return current_time()
                
            else:
                def get_t():
                    return getattr(parent.variables, time_var)

            self.get_t = get_t

            if custom_func is None:
                if absolute:
                    def new_calc(dt,
                                 slider_value):  # slider_value is a value between -1 & 1 depending on slider position
                        setattr(parent.variables, self.current_name,
                                getattr(parent.variables, self.current_name) + self.change_rate * slider_value * dt)

                else:
                    # scales logarithmically, so every dt*slider_value = 1 var gets multiplied by changerate
                    def new_calc(dt, slider_value):
                        setattr(parent.variables, self.current_name,
                                getattr(parent.variables, self.current_name) * self.change_rate ** (dt * slider_value))
            else:
                def new_calc(dt, slider_value):
                    setattr(parent.variables, self.current_name,
                            custom_func(getattr(parent.variables, self.current_name), dt, slider_value))

            self.new_calc = new_calc

            def update_func():
                if not self.slider.in_middle:
                    old_t = self.timer
                    self.timer = self.get_t()
                    dt = self.timer - old_t
                    slider_value = (self.slider.sliderPosition() - 100) / 100
                    # 6 is arbitrary, it's how changerate scales with slider_val, linear sucks
                    self.new_calc(dt, np.sign(slider_value) * (np.exp(np.abs(slider_value) * 6) - 1) / np.exp(6))
                    val = getattr(parent.variables, var_name)
                    parent.setItem(self.row, self.col, QTableWidgetItem(textify(val)))
            # </editor-fold>

            self.parent.window.on_refresh(update_func)

            if print_value:
                def print_func(row, col):
                    if row == self.row and col == self.col:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the rate_slider. Only keyword arguments are accepted, and takes all arguments that
            :func:`squap.add_rate_slider` accepts, except ``init_value`` and ``row``.
            """
            turn_on_print_func = False
            update_new_calc = False

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
                self._on_change(self.row, self.col)
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]
                self._on_change(self.row, self.col)

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.parent.cellChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True

            if "time_var" in kwargs:
                if kwargs["time_var"] != self.time_var:
                    if kwargs["time_var"] is None and self.time_var is not None:
                        self.timer = current_time()

                        def get_t():
                            return current_time()

                        self.get_t = get_t
                    elif kwargs["time_var"] is not None and self.time_var is None:
                        def get_t():
                            return getattr(self.parent.variables, self.time_var)

                        self.get_t = get_t
                    self.time_var = kwargs["time_var"]

            if "change_rate" in kwargs:
                self.change_rate = kwargs["change_rate"]

            if "absolute" in kwargs:
                self.absolute = kwargs["absolute"]
                update_new_calc = True

            if "custom_func" in kwargs:
                self.custom_func = kwargs["custom_func"]
                update_new_calc = True

            if update_new_calc:
                if self.custom_func is None:
                    if self.absolute:
                        def new_calc(dt,
                                     slider_value):  # slider_value is a value between -1 & 1 depending on slider position
                            setattr(self.parent.variables, self.current_name,
                                    getattr(self.parent.variables, self.current_name)
                                    + self.change_rate * slider_value * dt)

                    else:
                        # scales logarithmically, so every dt*slider_value = 1 var gets multiplied by changerate
                        def new_calc(dt, slider_value):
                            setattr(self.parent.variables, self.current_name,
                                    getattr(self.parent.variables, self.current_name) * self.change_rate ** (
                                                dt * slider_value))
                else:
                    def new_calc(dt, slider_value):
                        setattr(self.parent.variables, self.current_name,
                                self.custom_func(getattr(self.parent.variables, self.current_name), dt, slider_value))

                self.new_calc = new_calc

            if turn_on_print_func:
                self.parent.cellChanged.connect(self.print_val)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.parent.cellChanged.disconnect(func)
                    self.parent.cellChanged.connect(func)

        def bind(self, func):
            def new_func(row, col):
                if row == self.row and col == self.col:
                    func()

            self.change_funcs[func] = new_func
            self.parent.cellChanged.connect(new_func)
            return self

        def unbind(self, func):
            if func not in self.change_funcs and func != self._on_change:
                raise ValueError("Function is not bound to this Box.")
            if func != self._on_change:
                self.parent.cellChanged.disconnect(self.change_funcs[func])
                self.change_funcs.pop(func)
            else:
                self.parent.cellChanged.disconnect(self._on_change)
            return self

        def _on_change(self, row, col):
            if row == self.row and col == self.col:
                setattr(self.parent.variables, self.current_name, float(self.parent.item(self.row, self.col).text()))

        def value(self):
            return getattr(self.parent.variables, self.current_name)

        def set_value(self, value):
            setattr(self.parent.variables, self.current_name, value)
            self.parent.cellChanged.disconnect(self._on_change)
            self.parent.setItem(self.row, self.col, QTableWidgetItem(str(textify(value))))
            self.parent.cellChanged.connect(self._on_change)

        def print_val(self):
            print(f"{self.current_name} = {self.value()}")

    class ColorPicker(Box, ColorButton):
        """
        Class for the color_picker widget. See :func:`squap.add_color_picker` for initialisation information.
        """
        def __init__(self, parent: 'InputTable', name: str, init_value: ColorType, var_name: Optional[str] = None,
                     print_value: bool = False, row: Optional[int] = None):
            Box.__init__(self, parent)
            ColorButton.__init__(self)

            self.var_name = var_name

            # this bit is the same for most widgets:
            # <editor-fold desc="add_widget and init name&var_name">
            if name == "":  # if self.textbox will be created
                box_row = (self,)
            else:
                box_row = (self.textbox, self)
            row = parent.add_widget(row=row, box_row=box_row)
            self.row = row

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                col = 0
                parent.setSpan(row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                col = 1
                parent.setSpan(row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            parent.setCellWidget(row, col, self)
            # </editor-fold>
            self.current_name = var_name

            if init_value is None:
                self.set_value((0, 0, 0, 0))
            else:
                self.set_value(init_value)
            setattr(parent.variables, self.current_name, init_value)
            self.sigColorChanged.connect(self._on_change)

            if print_value:
                self.sigColorChanged.connect(self.print_val)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the color_picker. Only keyword arguments are accepted, and takes all arguments
            that :func:`squap.add_color_picker` accepts, except ``init_value`` and ``row``.
            """
            turn_on_print_func = False

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
                self._on_change()
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]
                self._on_change()

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.parent.cellChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True
            if turn_on_print_func:
                def print_func(row):
                    if row == self.row:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.parent.cellChanged.disconnect(func)
                    self.parent.cellChanged.connect(func)

        def bind(self, func):
            self.change_funcs[func] = func      # dict is not really necessary for this box, but not a problem either
            self.sigColorChanged.connect(func)
            return self

        def unbind(self, func):
            if func not in self.change_funcs and func != self._on_change:
                raise ValueError("Function is not bound to this Box.")
            if func != self._on_change:
                self.sigColorChanged.disconnect(self.change_funcs[func])
                self.change_funcs.pop(func)
            else:
                self.sigColorChanged.disconnect(self._on_change)

            return self

        def _on_change(self, *args):
            setattr(self.parent.variables, self.current_name, self.value())

        def set_value(self, value: ColorType):
            self.setColor(get_single_color(value))

        def value(self):
            return self.color(mode="float")

        def print_val(self):
            print(f"{self.current_name} = {self.value()}")
