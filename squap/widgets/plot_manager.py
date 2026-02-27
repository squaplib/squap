import numpy as np
from typing import Optional, Iterable, Union

from PySide6.QtWidgets import QTableWidget
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject

from .plot_widget import SubplotWidget


class FigWidget(QTableWidget):
    """Stores the plots and GraphicsLayoutWidget so that not everything is located inside the main window. The main
    window is only a window. """
    def __init__(self, parent):
        super().__init__(parent)

        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setStretchLastSection(True)

        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)

        self.plot_style_3D = False

        self.plot_widget = SubplotWidget(0, 0)
        self.axs = self.plot_widget                     # when there are no subplots, axs is the main plot widget
        self.shape = (1, 1)
        self.setRowCount(1)
        self.setColumnCount(1)

        self.setCellWidget(0, 0, self.plot_widget)

        self.widthratios = None                 # for subplots
        self.heightratios = None
        self.resize(*parent.size())

    def clear(self):
        if isinstance(self.axs, np.ndarray):
            for pw in self.axs.flatten():
                for curve in pw.curves:
                    pw.removeItem(curve)
        else:
            for curve in self.axs.curves:
                self.axs.removeItem(curve)

        self.plot_style_3D = False
        self.axs = SubplotWidget(0, 0)
        self.shape = (1, 1)
        self.setCellWidget(0, 0, self.axs)
        self.plot_widget = self.axs

        self.widthratios = None                 # for subplots
        self.heightratios = None
        super().clear()

    def update_size(self, event=None):
        if self.widthratios is not None:
            for index, widthratio in enumerate(self.widthratios):
                self.setColumnWidth(index, widthratio*self.width()-1)

            # pwidth = (self.width() - 18 - 6*(self.shape[1]-1))/sum(self.widthratios)
            # for index, width in enumerate(self.widthratios):
            #     self.setColumnWidth(index, pwidth * width)
        else:
            for i in range(self.shape[1]):
                self.setColumnWidth(i, int(self.width()/self.shape[1])-1)
        if self.heightratios is not None:
            for index, heightratio in enumerate(self.heightratios[:-1]):
                self.setRowHeight(index, heightratio*self.height()-1)
        else:
            for i in range(self.shape[0]):
                self.setRowHeight(i, int(self.height()/self.shape[0])-1)

    def resize(self, *args):
        if len(args) == 1:
            super().resize(args[0])  # QSize
        elif len(args) == 2:
            super().resize(args[0], args[1])  # width, height
        self.update_size()

    def create_subplots(
            self, nrows: int = 1, ncols: int = 1, heightratios: Optional[list[int]] = None,
            widthratios: Optional[list[int]] = None) -> list:
        """
        Initialises a subplot window and gives a 1D or 2D list of :class:`PlotWidgets <squap.widgets.plot_widget.PlotWidget>`.

        Args:
            nrows (int): number of rows.
            ncols (int): number of columns.
            heightratios (list of int, optional): ratios between the heights of the rows. Defaults to all ones. Only
                integer values allowed. Not working yet!(?)
            widthratios (list of int, optional): ratios between the widths of the columns. Defaults to all ones. Only
                integer values allowed. Not working yet!(?)

        Returns:
            list of :class:`PlotWidget <squap.widgets.plot_widget.PlotWidget>`: Possibly nested list of
            :class:`plot widgets <squap.widgets.plot_widget.PlotWidget>` on which different plots can be drawn.
        """
        if nrows == 1 and ncols == 1 and heightratios is None and widthratios is None:
            return self.axs

        self.setRowCount(nrows)
        self.setColumnCount(ncols)

        self.shape = (nrows, ncols)
        if widthratios is None:
            widthratios = [1]*ncols
        else:
            ncols = len(widthratios)
        if heightratios is None:
            heightratios = [1]*nrows
        else:
            nrows = len(heightratios)

        self.clear()            # removes all existing plots
        self.widthratios = np.array(widthratios)/sum(widthratios)           # normalise ratios
        self.heightratios = np.array(heightratios)/sum(heightratios)

        # pwidth = (self.width()-12)/sum(widthratios)-6
        # pheight = (self.height()-12)/sum(heightratios)-6
        width = self.width()
        height = self.height()

        self.axs = []
        if nrows == 1:
            for col in range(ncols):
                pw = SubplotWidget(0, col)
                self.axs.append(pw)
                self.setCellWidget(0, col, pw)
        elif ncols == 1:
            for row in range(nrows):
                pw = SubplotWidget(row, 0)
                self.axs.append(pw)
                self.setCellWidget(row, 0, pw)
        else:
            for row in range(nrows):
                axs_row = []
                for col in range(ncols):
                    pw = SubplotWidget(row, col)
                    axs_row.append(pw)
                    self.setCellWidget(row, col, pw)
                self.axs.append(axs_row)

        if heightratios:
            # Excludes last because the last stretches to fill, will be correct up to about 2 pixels
            for index, widthratio in enumerate(widthratios[:-1]):
                self.setColumnWidth(index, widthratio*width)
        if widthratios:
            # Excludes last because the last stretches to fill, will be correct up to about 2 pixels
            for index, heightratio in enumerate(heightratios[:-1]):
                self.setRowHeight(index, heightratio*height)

        self.axs = np.array(self.axs)
        return self.axs

    def remove_item(self, item: GraphicsObject):
        """
        Remove item ``item`` from the figure. Item can be anything that can be added to a plot widget.
        """
        if isinstance(self.axs, np.ndarray):
            for pw in self.axs.flatten():
                if item in pw.curves:
                    pw.removeItem(item)
            return
        else:
            if item in self.axs.curves:
                self.axs.removeItem(item)
                return
        raise ValueError("Item has not been found")

    def merge_plots(self, plots: Iterable[SubplotWidget]) -> SubplotWidget:  # not optimised, but fast enough (& not sure if it works)
        """Merge multiple :func:`subplots <squap.subplots>` into a single plot. This is used for unevenly spaced grids of subplots.

        Args:
            plots (list of :class:`SubplotWidget <squap.widgets.plot_widget.SubplotWidget>`): list of
                plots to merge.

        Returns:
            :class:`SubplotWidget <squap.widgets.plot_widget.SubplotWidget>`: One new
            :class:`plot object <squap.widgets.plot_widget.SubplotWidget>` in place of the merged plots.

        todo: adjust for QTableWidget
        """
        # hrs = list(np.cumsum(window.heightratios))
        # wrs = list(np.cumsum(window.widthratios))

        coordinates = []  # coordinates of plots, integer starting from 0, not accounting width and heights.
        for index, plt in enumerate(plots):
            coordinates.append((plt.row, plt.col))

        co_arr = np.array(coordinates)
        min_row, max_row = min(co_arr[:, 0]), max(co_arr[:, 0])
        min_col, max_col = min(co_arr[:, 1]), max(co_arr[:, 1])
        for x in range(min_row, max_row + 1):
            for y in range(min_col, max_col + 1):
                if (x, y) not in coordinates:
                    raise ValueError("The plots should form a rectangle")

        for co in coordinates:
            self.removeCellWidget(*co)

        # span = dif + 1
        self.setSpan(min_row, min_col, max_row - min_row + 1, max_col - min_col + 1)

        new_plot = SubplotWidget(min_row, min_col)

        self.setCellWidget(min_row, min_col, new_plot)
        return new_plot



