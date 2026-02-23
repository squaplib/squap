Custom Types
============

Currently there are two custom types you can encounter in this documentation:

.. _ColorType:

ColorType
---------

Any argument that can be used to make a color:

- ``str``: The name of a color. todo: list allowed colors.
- ``tuple``: An RGB tuple or an RGBA tuple. todo: hyperref and look up 0-1 or 0-255.
- ``float``: A single float represents a grayscale value, where ``0.0`` corresponds to black and ``1.0`` corresponds to white.
- ``mkColor``: A color object from the pyqtgraph library.
- ``QColor``: A color object from the PySide6 library.

.. _ColorsType:

ColorsType
----------

A possibly nested list containing any of the values accepted by :ref:`ColorType <ColorType>`.
