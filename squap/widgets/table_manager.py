from typing import Iterable, Optional, Callable, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from .input_widget import InputTable, Box            # only for type hinting
from ..helper_funcs import get_new_kwargs, ColorType


class TableManager:
    """Stores the table/tab widgets so that not everything is located inside the main window. The main
    window is only a window. """
    def __init__(self, height):
        self.width = 0
        self.height = height

        self.input_tables = []              # the input_widget, or all input tables in the QTabWidget if multiple tabs
        # are added
        self.main_input_widget = None       # the input_widget, or the QTabWidget if multiple tabs are added
        self.first_input_table = None       # the input_table that was added first
        self.resized = False                # if window is resized with existing input_widget but not yet shown, this is
        # set to True, so that showing doesn't correct for input_widget as normal

        self.tab_widget = None              # stuff that can be initialised later is set to None
        self.table_container = None

        self.input_partition = 1/3

        self.n_links = 0            # number of links between boxes

    def set_input_partition(self, fraction: float = 1/3):
        """Set the position of the partition between the 2 columns of all :class:`input tables <squap.widgets.input_widget.InputTable>`, and
        any newly created ones. Use :meth:`table.set_partition <squap.widgets.input_widget.InputTable.set_partition>` to set different
        partitions for different tables when you have multiple tabs.

        Args:
            fraction (float): value between ``0`` and ``1``, specifying the portion of the input table taken up by the
                text. Starts off at ``1/3``.
        """
        self.input_partition = fraction
        for table in self.input_tables:
            table.set_partition(fraction)

    def create_first_table(self, input_table):
        input_table.set_partition(self.input_partition)
        self.input_tables.append(input_table)

        self.first_input_table = input_table        # with one table, the first table is both the first table and the
        self.main_input_widget = input_table        # widget that needs to be resized.

        # First added table is added to a widget so that it can be moved into a QTabWidget later.
        self.table_container = QWidget()

        layout = QVBoxLayout(self.table_container)  # Set layout on the container
        layout.setContentsMargins(0, 0, 0, 0)       # Optional: Remove margins if needed
        layout.addWidget(input_table)               # Add table to the layout

        return input_table, self.table_container

    def init_tab_widget(self, window):
        self.tab_widget = QTabWidget()
        if self.resized:
            # print(self.size())
            width, height = window.size().toTuple()
            # copied from resize in __init__.py (when input_widget has been resized, the new QTabWidget is also resized)
            ratio = window.splitter.width_ratio
            self.tab_widget.resize(int(ratio * width / (ratio + 1)), height)
            window.plot_manager.fig_widget.resize(int(width / (ratio + 1)), height)
            window.splitter.resize(width, height)
        else:
            self.tab_widget.resize(self.width, window.height())

        self.main_input_widget = self.tab_widget
        self.table_container.deleteLater()
        window.splitter.replaceWidget(0, self.tab_widget)

        self.tab_widget.addTab(self.first_input_table, self.first_input_table.name)

    def add_table(self, new_table) -> InputTable:
        new_table.set_partition(self.input_partition)
        self.input_tables.append(new_table)
        self.tab_widget.addTab(new_table, new_table.name)
        return new_table

    def rename_tab(self, name: str, index: Optional[int] = 0, old_name: Optional[str] = None) -> InputTable:
        """
        Renames tab with index ``index`` or name ``old_name`` to ``name``.

        Args:
            name (str): New name.
            index (int, optional): Index of the tab you want to rename. Provide either ``index`` or ``old_name``.
            old_name (str, optional): Current name of the tab you want to rename.

        Returns:
            InputTable: The renamed :class:`table <squap.widgets.input_widget.InputTable>`.
        """
        if self.tab_widget is None:
            if index == 0 or old_name == self.first_input_table.name:
                self.first_input_table.name = name
            else:
                if old_name is not None:
                    raise ValueError(f"{old_name} is not the current name of a tab.")
                else:
                    raise ValueError(f"`index` is too high. It can be at most 0.")
            return self.first_input_table
        else:
            if old_name is not None:
                for i, table in enumerate(self.input_tables):
                    if table.name == old_name:
                        self.tab_widget.setTabText(i, name)
                        table.name = name
                        return table
                else:
                    raise ValueError(f"{old_name} is not the current name of a tab.")
            else:
                if index > len(self.input_tables):
                    raise ValueError(f"{index} is too high. It can be at most {len(self.input_tables)-1}.")
                self.input_tables[index].name = name
                self.tab_widget.setTabText(index, name)
                return self.input_tables[index]

    def set_active_tab(self, *args: int | InputTable | str, index: int | None = None, tab: InputTable | None = None,
                       name: str | None = None) -> InputTable:
        """Set active tab using one of the possible arguments. Use exactly one.

        Args:
            *args (int or InputTable or str, optional): One of the possible arguments, automatically determined which it is by
                given type.
            index (int, optional): Index of the tab to select. Defaults to ``None``.
            tab (InputTable, optional): The tab to select. Defaults to ``None``.
            name (str, optional): Name of the tab to select. Defaults to ``None``.

        Returns:
            InputTable: The :class:`InputTable <squap.widgets.input_widget.InputTable>` belonging to the selected tab.
        """
        if self.tab_widget is None:
            if self.first_input_table is None:
                raise ValueError("Could not find any tabs. Create tabs before selecting an active tab.")
            else:
                return self.first_input_table

        if args:
            if isinstance(args[0], int):
                index = args[0]
            elif isinstance(args[0], InputTable):
                tab = args[0]
            elif isinstance(args[0], str):
                name = args[0]
            else:
                raise ValueError("Type of arg not recognised. Must be `int` or `InputTable` or `str`, but"
                                 f" is {type(args[0])}.")

        if index is not None:
            self.tab_widget.setCurrentIndex(index)
        elif tab is not None:
            self.tab_widget.setCurrentWidget(tab)
        elif name is not None:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i).name == name:
                    self.tab_widget.setCurrentIndex(i)
                    break
        else:
            raise ValueError("`set_active_tab` needs an argument. ")
        return self.tab_widget.currentWidget()

    def on_tab_change(self, func: Callable):
        """Adds function ``func`` to the functions that are called whenever the current tab is changed. """
        self.tab_widget.currentChanged.connect(func)

    def get_current_row(self) -> int:
        """Return row of the latest placed widget."""
        return self.tab_widget.currentWidget().current_row

    def get_all_tabs(self) -> list[InputTable]:
        return self.input_tables

    def get_all_boxes(self) -> list[Box]:
        """
        Returns:
            list of Box: A list containing all :class:`boxes <squap.widgets.Box>` that exist at this time.
        """
        result = []
        for table in self.input_tables:
            result.extend(table.get_boxes())
        return result

    def link_boxes(self, boxes: Iterable[Box | int], only_update_boxes: list | None = None):
        """Link all boxes in the list `boxes`.

        Args:
            boxes (Iterable of Box or int): list of boxes or row numbers of the boxes to link
            only_update_boxes (list, optional): list of boxes are only updated when a box in boxes is
                changed but do not cause the other boxes to update when they are changed.
                `link_boxes(box1, box2); link_boxes(box2, box3)` can be used to link box1 to box2 and box2 to box3 without linking
                box1 to box3. todo: klopt niet helemaal
        """
        self.n_links += 1
        if only_update_boxes is None:
            only_update_boxes = []

        one_box_printing = False        # if multiple boxes are printing, all but one is turned off.
        for i, box_ in enumerate(boxes):
            # only_update_boxes enables linking box1 and box2 and box2 and box3 without
            # linking box1 and box3
            if box_ in only_update_boxes:
                def func():
                    return

            else:
                def func(*args, box=box_, n_links=self.n_links):
                    val = box.value()
                    for other_box in boxes:
                        if other_box != box and n_links in other_box.link_funcs.keys():
                            for link_func in other_box.link_funcs.values():      # prevents infinite recursion
                                other_box.unbind(link_func)
                            other_box.set_value(val)
                            for link_func in other_box.link_funcs.values():
                                other_box.bind(link_func)

                if box_.printing_val:
                    if one_box_printing:
                        box_.change_params(print_value=False)
                    else:
                        one_box_printing = True


            box_.link_funcs[self.n_links] = func
            box_.bind(func)

    def add_slider(self, name: str, init_value: float = 1.0, min_value: float = 0.0, max_value: float = 10.0,
                   n_ticks: int = 51, tick_interval: Optional[float] = None, only_ints: bool = False,
                   logscale: bool = False, custom_arr: Optional[Iterable] = None, var_name: Optional[str] = None,
                   print_value: bool = False, row: Optional[int] = None) -> 'InputTable.Slider | list[InputTable.Slider]':
        """Adds a :class:`slider <squap.widgets.input_table.InputTable.Slider>` to the main input widget, or to all
        :class:`input tables <squap.widgets.input_widget.InputTable>` if there are more.


        Args:
            name (str): The name in front of the slider.
            init_value (float): The initial value of the slider. If the provided value is not on the slider, it gets set
                to the closest value.
            min_value (float): The minimum value of the slider.
            max_value (float): The maximum value of the slider.
            n_ticks (int): The number of ticks on the slider. Defaults to ``51``.
            tick_interval (float, optional): The interval between ticks. If provided, overwrites ``n_ticks``.
            only_ints (bool): Whether to use whole numbers as ticks. If set to ``True``, ``tick_interval`` is used
                as spacing between the ticks and ``n_ticks`` is ignored. If ``tick_interval`` is not specified, it defaults
                to ``1``. Rounds ``tick_interval`` to an integer and changes the variable to always be an integer. Not allowed
                in combination with ``logscale``. Defaults to ``False``.
            logscale (bool): Whether to use a logarithmic scale. When ``tick_interval`` is given it serves as a
                multiplication factor between a point and the previous point (it is rounded to fit ``min_value`` and
                ``max_value``. Not allowed in combination with ``only_ints``. Defaults to ``False``.
            custom_arr (:term:`iterable`, optional): Array or list of values, where ``custom_arr[i]`` will be the value (can be
                any type) of the slider when it is set to position ``i``. Overwrites all other parameters (except
                ``init_value``). Defaults to ``None``.
            var_name (str, optional): The name of the created variable. If ``var_name`` is not provided, the variable will
                be named ``name``.
            print_value (bool): Whether to print the value of the slider when it changes. Defaults to ``False``.
            row (int, optional): Row to which the slider is added. Defaults to first empty row.

        Returns:
            InputTable.Slider or list of InputTable.Slider: The created
            :class:`slider widget(s) <squap.widgets.InputTable.Slider>`.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self"])

        if len(self.input_tables) > 1:
            boxes = []
            for table in self.input_tables:
                boxes.append(table.add_slider(**new_kwargs))

            self.link_boxes(boxes)
            return boxes
        else:
            return self.input_tables[0].add_slider(**new_kwargs)

    def add_checkbox(self, name: str, init_value: bool = False, var_name: Optional[str] = None,
                     print_value: bool = False, row: Optional[int] = None) -> 'InputTable.CheckBox | list[InputTable.CheckBox]':
        """Adds a :class:`checkbox <squap.widgets.input_table.InputTable.CheckBox>` to the main input widget, or to all
        :class:`input tables <squap.widgets.input_widget.InputTable>` if there are more.

        Args:
            name (str): The name in front of the checkbox.
            init_value (bool): The initial value of the checkbox. Defaults to ``False`` (not ticked).
            var_name (str, optional): The name of the created variable. If ``var_name`` is not provided, the variable will
                be named ``name``.
            print_value (bool): Whether to print the value of the checkbox when it changes. Defaults to ``False``.
            row (int, optional): Row to which the checkbox is added. Defaults to first empty row.

        Returns:
            InputTable.CheckBox or list of InputTable.CheckBox: The created
            :class:`checkbox widget(s) <squap.widgets.InputTable.CheckBox>`.
        """

        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self"])

        if len(self.input_tables) > 1:
            boxes = []
            for table in self.input_tables:
                boxes.append(table.add_checkbox(**new_kwargs))

            self.link_boxes(boxes)
            return boxes
        else:
            return self.input_tables[0].add_checkbox(**new_kwargs)

    def add_inputbox(self, name: str, init_value: Any = 1.0, type_func: Optional[Callable] = None,
                     var_name: Optional[str] = None, print_value: bool = False,
                     row: Optional[int] = None) -> 'InputTable.InputBox | list[InputTable.InputBox]':
        """Adds a :class:`inputbox <squap.widgets.input_table.InputTable.InputBox>` to the main input widget, or to all
        :class:`input tables <squap.widgets.input_widget.InputTable>` if there are more.

        Args:
            name (str): The name in front of the inputbox.
            init_value (optional): The initial value of the inputbox. Can be any object that can be turned into
                a string.
            type_func (:term:`callable`, optional): The function that takes in a string and returns the value as the
                correct type. Usually, this will default to :func:`ast.literal_eval`, which works for a lot of data
                types: :class:`str`, :class:`float`, :class:`complex`, :class:`bool`, :class:`tuple`, :class:`list`,
                :class:`dict`, :class:`set` and :obj:`None`.
                If ``type_func`` is set to ``None`` (default value), then it will be set to :func:`ast.literal_eval` if
                ``init_value`` is one of the mentioned data types. If ``init_value`` is a :class:`numpy.ndarray` or a :class:`range`
                object, this is also handled, but ``type_func`` needs to be explicitly changed to :func:`ast.literal_eval`
                if the data type is changed during runtime.
                If you have a different data type that doesn't work with the automatic behavior, a function can be
                passed to this argument that takes in a string and returns the desired value. Note that
                :func:`ast.literal_eval` is a lot slower than, for example, ``float``, so if you are sure the input is
                a float, a minor speedup can be achieved by explicitly setting ``type_func=float``.

                ``type_func`` can also be set to ``int``, so that each value is turned into an ``int``. If ``type_func``
                is not given, it is automatically determined, which works for the following instances: :class:`str`,
                :class:`float`, :class:`complex`, :class:`bool`, :class:`range`, and the following iterables:
                :class:`tuple`, :class:`list`, :class:`dict`, :class:`set` and :class:`numpy.ndarray`.
            var_name (str, optional): The name of the created variable. If ``var_name`` is not provided, the variable will
                be named ``name``.
            print_value (bool): Whether to print the value of the inputbox when it changes. Defaults to ``False``.
            row (int, optional): Row to which the inputbox is added. Defaults to first empty row.

        Returns:
            InputTable.InputBox or list of InputTable.InputBox: The created
            :class:`inputbox widget(s) <squap.widgets.InputTable.InputBox>`.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self"])

        if len(self.input_tables) > 1:
            boxes = []
            for table in self.input_tables:
                boxes.append(table.add_inputbox(**new_kwargs))

            self.link_boxes(boxes)
            return boxes
        else:
            return self.input_tables[0].add_inputbox(**new_kwargs)


    def add_button(self, name: str, func: Optional[Callable] = None, row: Optional[int] = None
                   ) -> 'InputTable.Button | list[InputTable.Button]':
        """Adds a :class:`button <squap.widgets.input_table.InputTable.Button>` to the main input widget, or to all
        :class:`input tables <squap.widgets.input_widget.InputTable>` if there are more.

        Args:
            name (str): The name in front of the button.
            func (:term:`callable`, optional): The function which is run on button press.
            row (int, optional): Row to which the button is added. Defaults to first empty row.

        Returns:
            InputTable.Button or list of InputTable.Button: The created
            :class:`button widget(s) <squap.widgets.InputTable.Button>`.
        """

        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self"])

        if len(self.input_tables) > 1:
            boxes = []
            for table in self.input_tables:
                boxes.append(table.add_button(**new_kwargs))

            self.link_boxes(boxes)
            return boxes
        else:
            return self.input_tables[0].add_button(**new_kwargs)

    def add_dropdown(self, name: str, options: list, init_index: int = 0, option_names: Optional[Iterable[str]] = None,
                     var_name: Optional[str] = None, print_value: bool = False, row: Optional[int] = None
                     ) -> 'InputTable.Dropdown | list[InputTable.Dropdown]':
        """Adds a :class:`dropdown <squap.widgets.input_table.InputTable.DropDown>` to the main input widget, or to all
        :class:`input tables <squap.widgets.input_widget.InputTable>` if there are more.

        Args:
            name (str): The name in front of the dropwdown.
            options (Iterable): A :class:`list` of all options the created variable can be, where
                ``option_names[index]`` is the value given to the variable, if the dropwdown is set to ``index``.
            init_index (int): The index that the dropwdown is initially set to.
            option_names (list of str, optional): A :class:`list` of all options shown in the dropwdown menu. If
                ``option_names`` is not provided it will be set to ``options``.
            var_name (str, optional): The name of the created variable. If ``var_name`` is not provided, the variable
                will be named ``name``.
            print_value (bool): Whether to print the value of the dropwdown when it changes. Defaults to ``False``.
            row (int, optional): Row to which the dropwdown is added. Defaults to first empty row.

        Returns:
            InputTable.Dropdown or list of InputTable.Dropdown: The created
            :class:`dropwdown widget(s) <squap.widgets.InputTable.Dropdown>`.
        """

        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self"])

        if len(self.input_tables) > 1:
            boxes = []
            for table in self.input_tables:
                boxes.append(table.add_dropdown(**new_kwargs))

            self.link_boxes(boxes)
            return boxes
        else:
            return self.input_tables[0].add_dropdown(**new_kwargs)

    def add_rate_slider(self, name: str, init_value: float = 1.0, change_rate: float = 10.0, absolute: bool = False,
                        time_var: Optional[str] = None, custom_func: Optional[Callable] = None,
                        var_name: Optional[str] = None, print_value: bool = False,
                        row: Optional[int] = None) -> 'InputTable.RateSlider | list[InputTable.RateSlider]':
        """Adds a :class:`rate slider <squap.widgets.input_table.InputTable.RateSlider>` to the main input widget, or to all
        :class:`input tables <squap.widgets.input_widget.InputTable>` if there are more.

        Args:
            name (str): The name in front of the rate slider.
            init_value (float): The initial value of the rate slider.
            change_rate (float): Change rate to the value of the variable per second. How it changes depends
                on ``absolute``.
            absolute (bool): How the value of the variable is changed. If ``absolute`` is ``True``, ``changerate``
                multiplied by the slider position (which is a value between ``-1`` and ``1`` will be added every second.
                If it is set to ``False``, the variable
                will be multiplied by ``changerate`` multiplied by the slider position every second.
            time_var (str, optional): If set to ``None`` (default), actual time will be used. It can also be set to the name of
                a variable in :class:`squap.var` as a string. Then that variable will be regarded as time: if it increases by 1,
                the variable belonging to this box will be changed by ``changerate``.
            custom_func (Callable, optional): the function that changes the created variable. Overrides ``absolute`` and ``change_rate``. It must
                take three arguments: ``old_value``, ``dt`` and ``slider_value`` and must return the new value. ``old_value`` is
                the value of the variable the previous time the function was run, ``dt`` is the change in time since then (takes
                ``time_var`` into account). ``slider_value`` is a value between ``-1`` and ``1``, dependent on the slider position.
            var_name (str, optional): The name of the created variable. If ``var_name`` is not provided, the variable will be
                named ``name``.
            print_value (bool): Whether to print the value of the slider when it changes. Defaults to ``False``.
            row (int, optional): Row to which the rate slider is added. Defaults to first empty row.

        Returns:
            InputTable.RateSlider or list of InputTable.RateSlider: The created
            :class:`rate_slider widget(s) <squap.widgets.InputTable.RateSlider>`.
        """

        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self"])

        if len(self.input_tables) > 1:
            boxes = []
            for table in self.input_tables:
                boxes.append(table.add_rate_slider(**new_kwargs))

            self.link_boxes(boxes)
            return boxes
        else:
            return self.input_tables[0].add_rate_slider(**new_kwargs)

    def add_color_picker(self, name: str, init_value: ColorType = (255, 255, 255), var_name: Optional[str] = None,
                         print_value: bool = False, row: Optional[int] = None
                         ) -> 'InputTable.ColorPicker | list[InputTable.ColorPicker]':
        """Adds a :class:`color picker <squap.widgets.input_table.InputTable.ColorPicker>` to the main input widget, or to all
        :class:`input tables <squap.widgets.input_widget.InputTable>` if there are more.


        Args:
            name (str): The name in front of the color picker.
            init_value (:ref:`ColorType`): The initial value of the color picker.
            var_name (str, optional): The name of the created variable. If ``var_name`` is not provided, the variable will be
                named ``name``.
            print_value (bool): Whether to print the value of the color picker when it changes. Defaults to ``False``.
            row (int, optional): Row to which the color picker is added. Defaults to first empty row.

        Returns:
            InputTable.ColorPicker or list of InputTable.ColorPicker: The created
            :class:`color_picker widget(s) <squap.widgets.InputTable.ColorPicker>`.
        """

        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self"])

        if len(self.input_tables) > 1:
            boxes = []
            for table in self.input_tables:
                boxes.append(table.add_color_picker(**new_kwargs))

            self.link_boxes(boxes)
            return boxes
        else:
            return self.input_tables[0].add_color_picker(**new_kwargs)
