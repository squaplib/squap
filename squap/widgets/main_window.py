import sys
import os.path
from time import perf_counter as current_time
import time
from argparse import Namespace

import imageio
import numpy as np

from typing import Callable, Optional

from PySide6.QtWidgets import QMainWindow, QSplitter, QApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QTimer, Qt

from .plot_manager import FigWidget
from .table_manager import TableManager
from .plot_widget import SubplotWidget
from .input_widget import InputTable
from .plot_widget_3D import SubplotWidget3D


class MainWindow(QMainWindow):
    def __init__(self, variables, width=640, height=480):
        self.app = QApplication()       # app must be created before QMainWindow initialisation.
        self.app.setStyle("Fusion")

        super().__init__()

        self.variables = variables
        self.update_funcs = []

        self.fig_widget = FigWidget(self)       # is also plot_manager
        self.setCentralWidget(self.fig_widget)

        self.table_manager = TableManager(height)       # initialising doesn't do much yet

        self.interval = None                # for timer when animated
        self.fps_timer = None
        self.refresh_timer = None
        self.timer = None                   # for disconnecting update_funcs

        self._updating = False              # flag that prevents recursion in align_camera
        self.resized = False                # if it has been resized already, the input_widget mustn't make it bigger
        self.splitter = None                # stuff that can be initialised later is set to None
        self.table_container = None         # For self.set_table_location
        self.exit_when_closed = False       # whether to exit the entire program when window is closed
        # (above is mainly useful for `while True: squap.refresh`)
        self.close_funcs = []
        self.on_key_press_funcs = []

        self.resize(width, height)

    def closeEvent(self, event=None):
        # Window is being closed
        for func in self.close_funcs:
            func()
        if self.exit_when_closed:       # not sure if there should be an else
            sys.exit("Application has been closed (code 1008)")

    def resizeEvent(self, event=None):
        self.fig_widget.update_size(event)
        self.table_manager.height = self.height()
        if event:
            event.accept()

    def keyPressEvent(self, event=None):
        for func in self.on_key_press_funcs:
            func(event)

        if event:
            event.accept()

    def pos(self):
        """Returns the position of the top-left of the window as numpy array in pixels."""
        return np.array(super().pos().toTuple())

    def clear(self):
        """Clear everything. Todo: check"""
        to_move = (np.array(self.size()) - np.array(self.fig_widget.size().toTuple()))/2
        self.move(*(self.pos() + to_move))
        self.resize(self.fig_widget.size())

        for update_func in self.update_funcs:
            self.timer.timeout.disconnect(update_func)

        self.update_funcs = []

        self.fig_widget.clear()
        self.fig_widget = FigWidget(self)
        self.setCentralWidget(self.fig_widget)

        self.table_manager.clear()
        self.table_manager = TableManager(self.height())
        self.resized = False
        self.splitter = None
        self.exit_when_closed = False       # whether to exit the entire program when window is closed
        self.close_funcs = []
        self.on_key_press_funcs = []

    def add_table(self, name: Optional[str] = None) -> InputTable:
        """
        Adds a new table as a tab with name ``name``.

        Returns:
            InputTable: The created :class:`table <squap.widgets.input_widget.InputTable>`.
        """
        if name is None:
            name = f"tab{len(self.table_manager.input_tables)+1}"
        if self.table_manager.main_input_widget is None:
            return self.init_first_tab(name=name)
        else:
            if self.table_manager.tab_widget is None:
                self.table_manager.init_tab_widget(self)
            new_table = InputTable(self.table_manager.width, self.table_manager.height, name, self)
            self.table_manager.add_table(new_table)
            return new_table

    def init_first_tab(self, width_fraction: float = 1/3, name: Optional[str] = None) -> InputTable:
        """
        Initialises the first tab and adds it to a widget so that it can be moved into a QTabWidget later. For the first
        tab we do not yet use a QTabWidget.

        Args:
            width_fraction (float): total width is ``3/2*normal width``, input widget size is ``width*width_fraction``.
                By default, width_fraction=0.5, probably meaning that
                fig_widget will be width 640, input_widget width 320, and window width 964. Note that width_fraction is a
                ratio not a fraction.
            name (str, optional): Name of the tab, only visible when multiple input tables are added.
        """
        if self.table_manager.first_input_table is not None:
            raise RuntimeError("Can not create a first table when one already exists, use `add_tab()` instead.")

        if name is None:
            name = f"tab{len(self.table_manager.input_tables)+1}"

        self.splitter = QSplitter()
        self.splitter.splitterMoved.connect(lambda: self.resizeEvent(None))     # sometimes when moving the split point,
        # the plot gets cut off. This is fixed here.
        self.table_manager.width_fraction = width_fraction

        # new_w = old_w*3/2
        self.table_manager.width = int(self.width()*3/2*width_fraction)
        table = InputTable(self.table_manager.width, self.table_manager.height, name, self)
        _, self.table_container = self.table_manager.create_first_table(table)
        # table container is stored for self.set_table_location

        self.splitter.addWidget(self.table_container)
        self.splitter.addWidget(self.fig_widget)
        self.setCentralWidget(self.splitter)

        height = self.height()
        if self.isVisible():
            self.resize(self.width() + self.table_manager.width + 4, height)
            # +4 extra for space between plot_widget and input_widget
            self.splitter.setSizes([self.table_manager.width, self.fig_widget.width()])

            pos = self.pos()
            self.move(int(pos[0] - 0.5 * (self.table_manager.width+4)), pos[1])

        return table

    def set_table_location(self, location: str = "left"):
        """
        Changes the side of the window on which the table is placed.

        Args:
            location: Which side the :class:`table <squap.widgets.input_widget.InputTable>` is placed on. Choose from
                ``"left"``, ``"right"``, ``"top"`` and ``"bottom"``. Defaults to ``"left"``

        """
        if self.table_manager.main_input_widget is None:
            self.init_first_tab()

        was_horizontal = self.location == "left" or self.location == "right"
        is_horizontal = location == "left" or location == "right"
        if was_horizontal and not is_horizontal:
            self.splitter.setOrientation(Qt.Orientation.Vertical)
            old_size = np.array(self.size())
            new_size = (old_size - np.array([4, 0]))*np.array([2/3, 3/2]) + np.array([0, 4])
            # self.splitter.setSizes()
            self.move(*(self.pos() + (old_size - new_size) / 2))
            self.resize(*new_size)
        elif not was_horizontal and is_horizontal:
            old_size = np.array(self.size())
            new_size = (old_size - np.array([0, 4]))*np.array([3/2, 2/3]) + np.array([4, 0])
            self.resize(*new_size)
            self.move(*(self.pos() + (old_size - new_size) / 2))
            self.splitter.setOrientation(Qt.Orientation.Horizontal)

        was_reversed = self.location == "right" or self.location == "bottom"
        is_reversed = location == "right" or location == "bottom"
        if not was_reversed and is_reversed:
            self.splitter.insertWidget(0, self.fig_widget)
            self.splitter.insertWidget(1, self.table_container)
        elif was_reversed and not is_reversed:
            self.splitter.insertWidget(0, self.table_container)
            self.splitter.insertWidget(1, self.fig_widget)
        self.location = location
        self.resizeEvent(None)


    # def init_3D(self):
    #     self.plot_style_3D = True
    #     self.plot_widget = PlotWidget3D(
    #         self.plot_widget.variables, self.plot_widget.update_funcs
    #     )
    #     self.setCentralWidget(self.plot_widget)

    def set_interval(self, interval: float):
        """Set interval between frames.

        Args:
            interval (float): The time interval (in seconds) to set for updating the plot.
        """
        self.interval = interval * 1000
        if self.is_alive():
            self.timer.setTimeout(self.interval)        # not tested

    def is_alive(self) -> bool:
        """Whether the window is visible. """
        return self.isVisible()

    def on_refresh(self, func: Callable, disconnect: bool = False):
        """Adds or removes a function that will be called on window refresh.

        Args:
            func (:term:`callable`): The function that will be called on refresh.
            disconnect (bool, optional): Whether the function should be connected (``False``) or disconnected (``True``).
                If you try to disconnect a function that cannot be disconnected, nothing happens. Defaults to False.
        """
        if not disconnect:
            if self.timer:
                self.timer.timeout.connect(func)
            self.update_funcs.append(func)
        else:
            if func in self.update_funcs:
                self.update_funcs.append(func)
                if self.timer:
                    self.timer.timeout.disconnect(func)

    def resize_window(self, width: int, height: int):
        """
        Resize the window.

        Args:
            width (int): Number of pixels wide it is changed to. Starts off at ``640``, or ``965`` if inputs are present
                (plot widget is 640, input widget 320 and border between them is 5 pixels.).
            height (int): New height in pixels. Starts off at ``480``.
        """
        self.resize(width, height)
        self.resized = True
        # if window.input_widget is None and not window.isVisible():
        #     window.fig_widget.resize(width, height)

        if self.table_manager.main_input_widget:
            fraction = self.table_manager.width_fraction
            self.table_manager.main_input_widget.resize(int(fraction*width), height)
            self.fig_widget.resize(int((1-fraction)*width), height)
            self.splitter.resize(width, height)
            self.table_manager.resized = True

    def size(self) -> tuple:
        """Returns the size of the window as a :class:`tuple` (width, height). Can be unreliable when called before
        the window is shown. """
        return super().size().toTuple()

    def set_input_width(self, fraction: float = 1/3):
        """
        Set the fraction of the window taken up by the input widget.

        Args:
            fraction (float, optional): value between ``0`` and ``1``, specifying the fraction of the window taken up by
                the input widget. Starts off at 1/3.
        """
        if not self.table_manager.first_input_table:
            self.init_first_tab(width_fraction=fraction)
        elif self.isVisible():
            width, height = self.size()
            self.table_manager.width_fraction = fraction
            self.table_manager.main_input_widget.resize(int(fraction * width), height)
            self.fig_widget.resize(int((1-fraction) * width), height)
            self.splitter.resize(width, height)
        else:
            width, height = self.size()
            width *= 3/2
            self.table_manager.width_fraction = fraction
            self.table_manager.main_input_widget.resize(int(fraction * width), height)
            self.fig_widget.resize(int((1-fraction) * width), height)
            self.splitter.resize(width, height)

    def refresh(self, wait_interval: bool = True, call_update_funcs: bool = True):
        """Refresh everything shown on screen, and wait according to interval (set with :func:`squap.set_interval`)

        Args:
            wait_interval (bool, optional): If set to ``False``, doesn't wait for time set by :func:`squap.set_interval`.
                Defaults to ``True``.
            call_update_funcs (bool, optional): If set to ``True``, calls all functions bound by :func:`squap.on_refresh` when
                this function is called. Defaults to ``True``.
        """
        if wait_interval and self.interval:
            now = current_time()
            to_wait = self.interval / 1000 - (now - self.refresh_timer)
            if to_wait > 0:
                time.sleep(to_wait)
            self.refresh_timer = current_time()
            QGuiApplication.processEvents()
        else:
            QGuiApplication.processEvents()
        if call_update_funcs:
            for func in self.update_funcs:
                func()
        # timer.start(0)

    def show_window(self):
        """Shows the window and refreshes it. It is Non-blocking, so use in combination with your own loop and
        :func:`squap.refresh`."""
        self.refresh_timer = current_time()

        if self.table_manager.main_input_widget:
            if self.resized:
                if not self.table_manager.resized:
                    fig_width = self.width() * (1-self.table_manager.width_fraction)
                    self.table_manager.width = fig_width * self.table_manager.width_fraction
                else:
                    fig_width = self.width() - self.table_manager.width - 4
                self.splitter.setSizes([self.table_manager.width, fig_width])
            else:
                if not self.table_manager.resized:
                    self.resize(self.width() + self.table_manager.width + 4, self.height())
                # +4 extra for space between plot_widget and input_widget
                self.splitter.setSizes([self.table_manager.width, self.fig_widget.width()])

        self.show()
        self.fig_widget.update_size()

        self.refresh()
        if self.interval:
            self.variables.hidden_variables["start"] = time.time()

            def interval_func():
                time_left = self.interval / 1000 - (time.time() - self.variables.hidden_variables["start"])
                print(f"{time_left = }")
                # the time it should still wait
                if time_left > 0:
                    time.sleep(time_left)
                self.variables.hidden_variables["start"] = time.time()

            self.update_funcs.append(interval_func)

    def start(self):
        """Shows window and starts loop. Use in combination with :meth:`squap.widgets.Box.bind`,
        :func:`squap.on_refresh` or for static plots. """
        timer = QTimer()  # timer is required for running functions on refresh and executing pyqtgraph programs
        if len(self.update_funcs):
            for func in self.update_funcs:
                timer.timeout.connect(func)

        if self.interval:
            timer.start(self.interval)
        else:
            timer.start()
        self.timer = timer

        if self.table_manager.main_input_widget:
            if self.resized:
                if not self.table_manager.resized:
                    fig_width = self.width() * (1-self.table_manager.width_fraction)
                    self.table_manager.width = fig_width * self.table_manager.width_fraction
                else:
                    fig_width = self.width() - self.table_manager.width - 4
                self.splitter.setSizes([self.table_manager.width, fig_width])
            else:
                if not self.table_manager.resized:
                    self.resize(self.width() + self.table_manager.width + 4, self.height())
                # +4 extra for space between plot_widget and input_widget
                self.splitter.setSizes([self.table_manager.width, self.fig_widget.width()])

            # pos = window.pos().toTuple()          # don't know why but this is suddenly not necessary anymore
            # window.move(pos[0]-0.5*(window.input_widget.width() + 4), pos[1])

        self.show()
        self.fig_widget.update_size()

        self.app.exec()

    def export(self, filename: str, widget: str = "window"):
        """Saves the current window as an image to file ``filename``.

        Args:
            filename (str): Name of the file to which the image must be saved. Extension can be png, jpg, jpeg, bmp, pbm,
                pgm, ppm, xbm and xpm. Defaults to png if no extension is provided.
            widget (str): The widget to export. The following options are available:

                    - ``"window"``: The full window.
                    - ``"plot"``: The plot window.
                    - ``"input"``: The input window.

                    Defaults to ``"window"``.

        """
        widget_map = {"window": self, "plot": self.fig_widget.plot_widget, "input": self.table_manager.table_container}
        widget_name = widget
        widget = widget_map[widget_name]
        pixmap = widget.grab()

        basename, extension = os.path.splitext(filename)
        if extension:
            success = pixmap.toImage().save(filename)
        else:
            success = pixmap.toImage().save(f"{filename}.png")
            extension = ".png"
        if success:
            print(f"Exported current {widget_name} window to {basename}{extension}")
        else:
            raise RuntimeError(f"Saving failed, probably because extension {extension} is not an allowed extension")

    def export_video(
            self, filename: str, fps: float = 30.0, n_frames: Optional[int] = None, duration: Optional[float] = None,
            stop_func: Optional[Callable] = None, skip_frames: int = 0, display_window: bool = False,
            widget: str = "window", save_on_close: bool = False
    ):
        """Saves a video to file ``filename`` with the specified parameters.

        Out of ``n_frames``, ``duration`` and ``stop_func`` at most one can be provided. If none of these are given, the video
        will be indefinite, and will be stopped and saved as soon as the window is closed, or when :exc:`KeyboardInterrupt` is
        raised (when the user attempts to manually stop the program).

        Args:
            filename (str): Name of the file to which the video will be exported.
            fps (float, optional): Frames per second of the video. Defaults to ``30``.
            n_frames (int, optional): Number of frames before the video stops and saves.
            duration (float, optional): Duration in seconds before the video stops and saves. It will save the last frame
                after the time is up as well.
            stop_func (:term:`callable`, optional): This function will be run after every iteration. If it returns True, the video
                stops and saves.
            save_on_close (bool): Whether to save the video if the window is closed prematurely. Defaults to ``False``,
                except when neither ``n_frames``, ``duration`` nor ``stop_func`` are provided.
            skip_frames (int): Number of frames to not save after a frame is saved. Defaults to ``0``.
            display_window (bool): Whether to display the window or not. Defaults to ``False``.
            widget (str): The widget to export. The following options are available:

                    - ``"window"``: The full window.
                    - ``"plot"``: The plot window.
                    - ``"input"``: The input window.

                    Defaults to ``"window"``.

        """
        # save_on_close is False by default so that you don't accidentally overwrite a video that took very long to make.
        widget_map = {"window": self, "plot": self.fig_widget, "input": self.table_manager.table_container}
        widget_name = widget
        widget = widget_map[widget_name]

        if len([None for arg in [n_frames, duration, stop_func] if arg is None]) < 2:
            raise ValueError("Only one of n_frames, duration or stop_func can be provided, error code 1009.")

        # this bit creates the loop condition, which can be the stop_func given by the user, or
        if duration is not None:
            n_frames = int(duration * fps)
        if stop_func is not None:
            def condition():
                return stop_func()
        elif n_frames is None:
            def condition():
                return False
        else:
            n_frames = int(n_frames)  # shouldn't do anything, but just incase it prevents an infinite loop
            save_on_close = True

            def condition():
                return frame_counter == n_frames

        frame_counter = 0
        pixmaps = []
        if display_window:
            self.show_window()

        try:
            while not condition():
                for update_func in self.update_funcs:
                    update_func()

                if display_window:
                    self.refresh()

                if not frame_counter % (skip_frames + 1):
                    pixmaps.append(widget.grab())

                frame_counter += 1

        except KeyboardInterrupt:
            if save_on_close:
                print("The program is interupted, the recording is now being save.")
            else:
                print("The program is interupted, the video will not be saved.")
                return

        basename, extension = os.path.splitext(filename)
        if not extension:
            extension = ".mp4"
        print(f"started saving {len(pixmaps)} frames to file {basename}{extension} at {fps} fps")

        arrs = []

        for index, pixmap in enumerate(pixmaps):
            qimg = pixmap.toImage()

            img_size = qimg.size()
            buffer = qimg.constBits()

            arr = np.ndarray(
                shape=(img_size.height(), img_size.width(), qimg.depth() // 8),
                buffer=buffer,
                dtype=np.uint8
            )
            arrs.append(arr[:, :, :3])  # only include RGB, not A

        try:
            width, height, _ = arr.shape
        except NameError:
            raise NameError("No frames were captured, error code 1006.")

        imageio.mimsave(f"{basename}{extension}", arrs, fps=fps, macro_block_size=1)

        print("Saving finished.")

    def start_recording(self, filename: str, fps: float = 30.0, skip_frames: int = 0,
                        widget: str = "window") -> Callable:
        """Start recording to file ``filename`` with the specified parameters. Use function returned by this function to stop
        the recording.

        Args:
            filename (str): Name of the file to which the video will be exported.
            fps (float): Frames per second of the video. Defaults to 30.
            skip_frames (int): number of frames to not save after a frame is saved. Defaults to 0.
            widget (str): The widget to export. The following options are available:

                    - ``"window"``: The full window.
                    - ``"plot"``: The plot window.
                    - ``"input"``: The input window.

                    Defaults to ``"window"``.

        Returns:
            :term:`callable`: Call this function to stop the recording and save the video.
        """
        widget_map = {"window": self, "plot": self.fig_widget, "input": self.table_manager.table_container}
        widget_name = widget
        widget = widget_map[widget_name]

        pixmaps = []
        frame_counter = {"i": 0}

        def record_func():
            if not frame_counter["i"] % (skip_frames + 1):
                pixmaps.append(widget.grab())
            frame_counter["i"] += 1

        def stop_func():
            basename, extension = os.path.splitext(filename)
            print(
                f"started saving {len(pixmaps)} frames to file {basename}{extension} at {fps} fps")
            if not extension:
                extension = f".mp4"

            arrs = []

            for index, pixmap in enumerate(pixmaps):
                qimg = pixmap.toImage()

                img_size = qimg.size()
                buffer = qimg.constBits()

                arr = np.ndarray(
                    shape=(img_size.height(), img_size.width(), qimg.depth() // 8),
                    buffer=buffer,
                    dtype=np.uint8
                )
                arrs.append(arr[:, :, :3])  # only include RGB, not A

            try:
                width, height, _ = arr.shape
            except NameError:
                raise NameError("No frames were captured, error code 1006.")

            imageio.mimsave(f"{basename}{extension}", arrs, fps=fps, macro_block_size=1)

            print("Saving finished.")

            self.update_funcs.remove(record_func)

        self.update_funcs.append(record_func)

        return stop_func

    def display_fps(self, update_speed: float = 0.2, get_fps: bool = False, optimized: bool = False,
                    ax: Optional[SubplotWidget] = None):
        """
        Display frames per second (fps) at the top of the :class:`plot widget <squap.widgets.plot_widget.SubplotWidget>`.

        Args:
            update_speed (float): The update speed for fps calculation. Defaults to ``0.2`` seconds.
            get_fps (bool): Whether to store the fps. If set to ``True``, the fps will be saved to
                :ref:`var.fps <squap.var>` every time it is updated. Defaults to ``False``.
            optimized (bool): Whether to use an optimized calculation method. If set to ``True``, it is a bit
                quicker, but less consistent for variable fps. Defaults to ``False``.
            ax (:class:`SubplotWidget <squap.widgets.plot_widget.SubplotWidget>`, optional): Which window to set the title to the fps. Defaults to top-left.

        Returns:
            :term:`callable`: Function that is needed to update the fps. If the program is run using :func:`squap.show`,
            this is handled automatically, but when you use :func:`squap.show_window`, it needs to be run with
            :func:`squap.refresh`, either manually or by calling :func:`squap.refresh(call_update_funcs=True) <squap.refresh>`.

        Raises:
            :exc:`NotImplementedError`: If the function is called in 3D plot style, which is not supported yet.
        """
        if ax is None:
            ax = self.fig_widget.plot_widget

        self.fps_timer = current_time()
        skip = Namespace(total=0, count=0)  # Namespace used for function variables that need to carry over
        # the fps is updated

        if optimized:
            def func():
                if skip.count == 0:
                    now = current_time()
                    elapsed = now - self.fps_timer
                    if elapsed:
                        self.fps_timer = now
                        fps = (skip.total + 1) / elapsed
                        fps = round(fps, -int(np.floor(np.log10(fps))) + (5 - 1))
                        if get_fps:
                            setattr(self.variables, "fps", fps)
                        if self.fig_widget.plot_style_3D:
                            print(f"{fps = }")
                        else:
                            ax.set_title(f"fps = {fps}")

                        skip.total = int(update_speed * fps)
                        skip.count = skip.total
                else:
                    skip.count -= 1
        else:
            def func():
                elapsed = current_time() - self.fps_timer
                skip.count += 1
                if elapsed > update_speed:
                    self.fps_timer = current_time()
                    fps = skip.count / elapsed
                    fps = round(fps, -int(np.floor(np.log10(fps))) + (5 - 1))
                    if isinstance(ax, SubplotWidget3D):
                        print(f"{fps = }")
                    else:
                        ax.set_title(f"fps = {fps}")
                    skip.count = 0

        self.update_funcs.append(func)  # both so that it works for both styles

    def benchmark(self, n_frames: Optional[int] = None, duration: Optional[float] = None):
        """Run the program until it is closed and then report the total frames and fps.

        If ``n_frames`` or ``duration`` are specified, the program will quit when either has passed.

        Args:
            n_frames (int, optional): Number of frames to run the program for.
            duration (float, optional): Total time to run the program for in seconds.
        """
        local_vars = Namespace(time=current_time(), count=0)
        # Namespace used for function variables that need to carry over

        if n_frames is None and duration is None:
            def func():
                local_vars.count += 1

        elif n_frames is None:
            def func():
                local_vars.count += 1
                if current_time() - local_vars.time > duration:
                    self.close()

        elif duration is None:
            def func():
                local_vars.count += 1
                if local_vars.count >= n_frames:
                    self.close()

        else:
            def func():
                local_vars.count += 1
                if current_time() - local_vars.time > duration or local_vars.count >= n_frames:
                    self.close()

        def final_func():
            elapsed = current_time() - local_vars.time
            print(f"{local_vars.count} frames have passed in {elapsed} seconds, "
                  f"which gives an fps of {local_vars.count / elapsed}")

        self.update_funcs.append(func)
        self.close_funcs.append(final_func)

    def on_key_press(self, func: Callable, accept_modifier: bool = False, modifier_arg: bool = False,
                     event_arg: bool = False) -> Callable:
        """Bind ``func`` to keypress. ``func`` takes as argument which key is pressed. This function is not great yet
        but good enough for simple stuff. For complex stuff look into event_arg for now.

        Args:
            func (:term:`callable`): The function that is called when the key is pressed.
            accept_modifier (bool): Whether to call the function when the input is a modifier, such as shift or
                alt. Defaults to ``False``.
            modifier_arg (bool): Whether to call the function with the modifier as an extra argument. Defaults to
                ``False``.
            event_arg (bool): Whether to call the function with just the event as an argument. This is more complex
                to deal with but much more versatile. Defaults to ``False``.

        Returns:
            :term:`callable`: The edited function that accepts the arguments listed above.
        """
        if self.keyboardGrabber() is None:
            self.grabKeyboard()

        if event_arg:  # needs no changes, func takes as argument the event.
            edited_func = func
        else:
            def edited_func(event):  # edited_func takes in event, while func takes in func
                key = event.key()
                print(key)
                if not key & (1 << 24):
                    key = chr(key)
                if event.modifiers() == Qt.NoModifier:
                    if modifier_arg:
                        func(key, None)
                    else:
                        func(key)
                else:
                    if modifier_arg:
                        func(key, event.modifiers())
                    else:
                        if accept_modifier:
                            func(event.modifiers())

        self.on_key_press_funcs.append(edited_func)
        return edited_func

    def align_camera(self, ax: Optional[SubplotWidget3D] = None, tab: Optional[InputTable | str] = None):
        """Adjusts camera position of a 3D plot. Use this to find the correct parameters to set the desired initial
        camera position with :func:`squap.set_camera`.

        Args:
            ax (SubplotWidget3D, optional): Specifies the plot which the control boxes control. Defaults to the main plot.
            tab (InputTable or str, optional): The tab to which to add the control boxes, or a string that represents
                the name of the newly created tab which the control boxes will be added to. Defaults to the main input
                table.
        """

        if tab is None:
            tab = self.table_manager.main_input_widget
        elif isinstance(tab, str):
            tab = self.add_table(tab)

        if ax is None:
            ax = self.fig_widget.plot_widget

        current_params = ax.cameraParams()
        current_pos = ax.camera_pos
        var = self.variables

        def update_cam():
            ax.set_camera(
                distance=var.distance, azimuth=var.azimuth, elevation=var.elevation, fov=var.fov,
                x_offset=var.x_offset, y_offset=var.y_offset, z_offset=var.z_offset, _emit_camera_changed=False
            )

        boxes = [
            tab.add_rate_slider("distance", current_params["distance"], change_rate=2),
            tab.add_slider("azimuth", current_params["azimuth"], 0, 360, n_ticks=72),
            tab.add_slider("elevation", current_params["elevation"], -90, 90, n_ticks=180),
            tab.add_slider("fov", current_params["fov"], 0, 180, n_ticks=180),
            tab.add_rate_slider("x_offset", current_pos[0], absolute=True, change_rate=5),
            tab.add_rate_slider("y_offset", current_pos[1], absolute=True, change_rate=5),
            tab.add_rate_slider("z_offset", current_pos[2], absolute=True, change_rate=5),
        ]

        for box in boxes:
            box.bind(update_cam)

        update_cam()

        def get_params():
            print(
                f"The following function would get you the current camera postition: \n"
                f"squap.set_camera(\n"
                f"    x_offset={var.x_offset}, y_offset={var.y_offset}, z_offset={var.z_offset}, \n"
                f"    distance={var.distance}, azimuth={var.azimuth}, elevation={var.elevation}, fov={var.fov}\n)"
            )

        tab.add_button("print camera parameters", get_params)

        def _do_update():
            current_params_ = ax.cameraParams()
            current_pos_ = current_params_["center"].toTuple()
            box_values = [current_params_["distance"], current_params_["azimuth"]%360, current_params_["elevation"],
                          current_params_["fov"], *current_pos_]
            for i, (box_, box_value) in enumerate(zip(boxes, box_values)):
                box_.set_value(box_value)

        ax.cameraChanged.connect(_do_update)