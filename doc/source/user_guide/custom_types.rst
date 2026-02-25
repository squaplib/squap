Custom Types
============

Currently there are two custom types you can encounter in this documentation:

.. _ColorType:

ColorType
---------

Any argument that can be used to make a color:

- :class:`str`: A hex code, or the name of a color. todo: list allowed colors.
- :class:`tuple`: An RGB or RGBA tuple containing 3 or 4 floats between 0 and 1.
- :class:`float`: A single float represents a grayscale value, where ``0.0`` corresponds to black and ``1.0`` corresponds to white.
- :class:`int`: One of 8 presets. ``0`` is red, ``1`` is orange, and so on.
- :class:`mkColor <pyqtgraph.mkColor>`: A color object from the pyqtgraph library.
- :class:`QColor <PySide6.QtGui.QColor>`: A color object from the PySide6 library.

.. _ColorsType:

ColorsType
----------

A possibly nested list containing any of the values accepted by :ref:`ColorType <ColorType>`. Also accepts a single
:ref:`ColorType <ColorType>` value.
