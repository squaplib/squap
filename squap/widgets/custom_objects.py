### Relatively new file. Meant for objects that are changed significantly from the pyqtgraph implementation.
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
from pyqtgraph import GridItem, mkPen
from pyqtgraph import functions as fn

from PySide6.QtGui import QFontMetricsF
from PySide6.QtCore import Qt

from ..customisation import Font


class SyncedGridItem(GridItem):
    def __init__(self, var):
        super().__init__()
        self.sync_axes = True
        self.base = 10
        self.thick_axes = True

        self.font = Font(font_size=11)
        self.axPen = mkPen(self.opts["pen"])
        self.axPen.setColor("white")
        self.axPen.setWidth(1)
        self.variables = var


    def generatePicture(self):
        lvr = self.boundingRect()
        device_transform = self.deviceTransform_()
        if lvr.isNull() or device_transform is None:
            return

        self.picture = QtGui.QPicture()
        p = QtGui.QPainter()
        p.begin(self.picture)

        vr = self.getViewWidget().rect()
        unit = np.array([self.pixelWidth(), self.pixelHeight()])
        dim = [vr.width(), vr.height()]
        ul = np.array([lvr.left(), lvr.top()])
        br = np.array([lvr.right(), lvr.bottom()])

        texts = []

        if ul[1] > br[1]:
            x = ul[1]
            ul[1] = br[1]
            br[1] = x

        lastd = [None, None]
        for i in range(self.grid_depth - 1, -1, -1):
            dist = br - ul
            nlTarget = 10. ** i
            if self.sync_axes:
                dist = np.array([np.sqrt(np.prod(dist))]*2)
            d = self.base ** np.floor(np.log10(np.abs(dist / nlTarget)) + 0.5)
            for ax in range(0, 2):
                ts = self.opts['tickSpacing'][ax]
                try:
                    if ts[i] is not None:
                        d[ax] = ts[i]
                except IndexError:
                    pass
                lastd[ax] = d[ax]

            ul1 = np.floor(ul / d) * d
            br1 = np.ceil(br / d) * d
            dist = br1 - ul1
            nl = (dist / d) + 0.5
            for ax in range(0, 2):  ## Draw grid for both axes
                ppl = dim[ax] / nl[ax]
                c = int(fn.clip_scalar(5 * (ppl - 3), 0, 50))

                if i >= len(self.opts['tickSpacing'][ax]):
                    continue
                if d[ax] < lastd[ax]:
                    continue

                linePen = self.opts['pen']
                lineColor = self.opts['pen'].color()
                lineColor.setAlpha(c)
                linePen.setColor(lineColor)

                textPen = self.opts['textPen']
                if textPen is not None:
                    textColor = self.opts['textPen'].color()
                    textColor.setAlpha(c * 2)
                    textPen.setColor(textColor)

                bx = (ax + 1) % 2
                for x in range(0, int(nl[ax])):
                    linePen.setCosmetic(True)
                    p.setPen(linePen)
                    p1 = np.array([0., 0.])
                    p2 = np.array([0., 0.])
                    p1[ax] = ul1[ax] + x * d[ax]
                    p2[ax] = p1[ax]
                    p1[bx] = ul[bx]
                    p2[bx] = br[bx]
                    ## don't draw lines that are out of bounds.
                    if p1[ax] < min(ul[ax], br[ax]) or p1[ax] > max(ul[ax], br[ax]):
                        continue

                    if p1[ax] == 0:
                        p.setPen(self.axPen)
                    else:
                        p.setPen(linePen)

                    p.drawLine(QtCore.QPointF(p1[0], p1[1]), QtCore.QPointF(p2[0], p2[1]))
                    if i < 2 and textPen is not None:
                        if p1[ax] == 0 and ax == 1:
                            pass  # skip duplicate "0" already drawn by the ax==0 pass
                        else:
                            label = "%g" % p1[ax]
                            text_size = np.array(QFontMetricsF(self.font).size(
                                Qt.TextFlag.TextSingleLine, label).toTuple())*unit       # text size in coordinates
                            text_size[0] *= 1.15        # Determined by hand. Puts the numbers on the bottom left.
                            text_size[1] *= 0.7
                            if ax == 0:
                                x = p1[0]
                                y = fn.clip_scalar(0.0, ul[1], br[1])
                            else:
                                x = fn.clip_scalar(0.0, ul[0], br[0])
                                y = p1[1]
                            texts.append((QtCore.QPointF(x - text_size[0], y - text_size[1]), label))

        p.setWorldTransform(fn.invertQTransform(device_transform))

        if textPen is not None and len(texts) > 0:
            # if there is at least one text, then c is set
            textColor.setAlpha(c * 2)
            p.setPen(QtGui.QPen(textColor))
            p.setFont(self.font)
            for t in texts:
                x = device_transform.map(t[0]) + Point(0.5, 0.5)
                p.drawText(x, t[1])

        p.end()
