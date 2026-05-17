from pyqtgraph.opengl import GLViewWidget, GLGridItem
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QVector3D

import numpy as np
from typing import Iterable, Optional

from ..helper_funcs import get_new_kwargs, ColorType, ColorsType
from .curves_3D import ScatterCurve3D, Mesh, SphereMesh, CubeMesh
from numpy.typing import NDArray


class SubplotWidget3D(GLViewWidget):
    """Widget for 3D plots. Obtain from :func:`squap.make_3D`"""
    def __init__(self, row: int, col: int, **kwargs):
        super().__init__(**kwargs)
        self.row = row          # for merging subplots
        self.col = col
        self.curves = []        # for clearing curves
        self.zoom_rate = 1.003
        self.camera_pos = np.array([.0, .0, .0])

        # change the size policy, so it is the same as a regular plot widget
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(size_policy)

    def add_curve(self, curve):
        self.addItem(curve)

    def wheelEvent(self, ev):       # changes default to changing distance instead of fov
        angledelta = ev.angleDelta()
        delta = -angledelta.x()-angledelta.y()
        self.opts["distance"] *= self.zoom_rate**delta

        self.update()

    def set_camera(self,
                   x_offset: Optional[float] = None, y_offset: Optional[float] = None, z_offset: Optional[float] = None,
                   distance: Optional[float] = None, azimuth: Optional[float] = None,
                   elevation: Optional[float] = None, fov: Optional[float] = None):
        """
        Sets the camera offset, distance, rotation and fov using the given arguments. ``distance``, ``azimuth`` and
        ``elevation`` act like polar coordinates around the origin, and ``x_offset``, ``y_offset`` and ``z_offset``
        determine the position of this origin.
        Use :func:`squap.align_camera` to experiment with these values and find the correct ones.

        Args:
            x_offset (float, optional): New x offset of the origin.
            y_offset (float, optional): New y offset of the origin.
            z_offset (float, optional): New z offset of the origin.
            distance (float, optional): New distance between the camera position and the origin.
            azimuth (float, optional): Angle of rotation horizontally around the origin.
            elevation (float, optional): Angle of rotation vertically about the origin.
            fov (float, optional): Field of view.
        """
        cam_params_kwargs = {}

        if distance is not None:
            cam_params_kwargs["distance"] = distance
        if azimuth is not None:
            cam_params_kwargs["azimuth"] = azimuth
        if elevation is not None:
            cam_params_kwargs["elevation"] = elevation
        if fov is not None:
            cam_params_kwargs["fov"] = fov

        self.setCameraParams(**cam_params_kwargs)
        if x_offset is not None or y_offset is not None or z_offset is not None:
            if x_offset is not None:
                self.camera_pos[0] = x_offset
            if y_offset is not None:
                self.camera_pos[1] = y_offset
            if z_offset is not None:
                self.camera_pos[2] = z_offset
            self.setCameraPosition(
                QVector3D(*self.camera_pos)
            )

    def set_zoom_rate(self, new_rate: float = 1.003):
        """Sets the rate at which you zoom when the plot is zoomed after it has been created.
        Starts off at ``1.003``.
        """
        self.zoom_rate = new_rate

    def add_grid(self, diagonal: tuple[float], spacing: float = 1) -> GLGridItem:
        """
        Adds a grid that lies on or parallel to one of the planes.

        Args:
            diagonal (tuple of float): A tuple of two coordinates that span the diagonal of a rectangle that lies on or
                parallel to the xy, yz, or zx plane.
            spacing (float): Spacing between the grid lines. Defaults to 1.

        Returns:
            :class:`~pyqtgraph.opengl.GLGridItem`: The created grid.
        """
        diagonal = np.array(diagonal)

        size_arr = (np.abs(diagonal[0, :] - diagonal[1, :]))  # difference between diagonals
        size = [i for i in size_arr if i != 0]  # size without 0's.

        if len(size) != 2:
            if len(size) == 3:
                raise ValueError(
                    f"The given diagonal is not the diagonal of a rectangle that lies parallel to the xy, "
                    f"yz or zx plane. Try using `add_complex_grid`.")
            else:
                raise ValueError(f"The given diagonal lies on a straight line, parrallel to the axis.")

        grid = GLGridItem()
        grid.setSize(*size)
        if size_arr[0] == 0:  # checks in which plane it lies
            grid.rotate(90, 0, 0, 1)  # this one needs to be rotated 90 degrees in the xy plane first
            grid.rotate(90, 0, 1, 0)
        if size_arr[1] == 0:
            grid.rotate(90, 1, 0, 0)

        bot_corner = np.min(diagonal, axis=0)  # bottom corner of the rectangle spanned by the diagonals.
        grid.translate(*(size_arr / 2 + bot_corner))
        self.curves.append(grid)
        self.addItem(grid)
        grid.remove = lambda: self.removeItem(grid)
        grid.setSpacing(x=spacing, y=spacing, z=spacing)
        return grid

    def add_grids(self, size: tuple[float], spacing: float = 1) -> list[GLGridItem]:    # maybe change to grids with max_x, max_y and max_z
        """
        Adds square grids on the xy, yz and zx planes, spanning from ``size[0]`` to ``size[1]``.

        Args:
            size (tuple of float): the size of each grid.
            spacing (float): Spacing between the grid lines. Defaults to 1.

        Returns:
            list of :class:`~pyqtgraph.opengl.GLGridItem`: The created grids.
        """
        grids = [
            self.add_grid(((size[0], size[0], 0), (size[1], size[1], 0))),
            self.add_grid(((size[0], 0, size[0]), (size[1], 0, size[1]))),
            self.add_grid(((0, size[0], size[0]), (0, size[1], size[1])))
        ]
        for grid in grids:
            grid.setSpacing(x=spacing, y=spacing, z=spacing)

        return grids

    def scatter(self, x: Optional[Iterable] = None, y: Optional[Iterable] = None, z: Optional[Iterable] = None,
                pos: Optional[NDArray] = None, color: ColorsType = "y", size: int | Iterable[int] = 4,
                pixel_mode: bool = True, **kwargs):
        """
        Creates a new scatter plot item. Use either ``x``, ``y`` and ``z`` or ``pos`` to set the coordinates of the
        points.

        Args:
            x (:class:`np.ndarray <numpy.ndarray>`, optional): New x-locations of each point. Defaults to ``None``,
                which means the data will be initialised with ``pos``, or it will be initialised later.
            y (:class:`np.ndarray <numpy.ndarray>`, optional): New y-locations of each point. Defaults to ``None``,
                which means the data will be initialised with ``pos``, or it will be initialised later.
            z (:class:`np.ndarray <numpy.ndarray>`, optional): New z-locations of each point. Defaults to ``None``,
                which means the data will be initialised with ``pos``, or it will be initialised later.
            pos (:class:`np.ndarray <numpy.ndarray>`, optional): Shape ``(N, 3)`` (:class:`array <numpy.ndarray>`) of floats
                specifying point locations. Can be used instead of ``x``, ``y`` and ``z``.
            color (:ref:`ColorsType`): Changes the color of the points. See :ref:`ColorsType`
                for allowed values.
            size (int or list of int): The size of the scatter plot points. Also accepted as ``s``. Default is ``4``.
            pixel_mode (bool): Whether to fix the size of each point. If ``True``, size is specified
                in pixels. If ``False``, size is specified in data coordinates. Defaults to ``True``.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["x", "y", "z", "pos"],
                                    exclude_args=["self", "kwargs"])

        curve = ScatterCurve3D()
        curve.set_data(**new_kwargs, **kwargs)
        self.add_curve(curve)
        return curve

    def mesh(self, vertexes: Optional[NDArray] = None, faces: Optional[NDArray] = None,
             color: ColorType = (1, 1, 1, 0.1), draw_edges: bool = False, draw_faces: bool = True,
             shader: Optional[str] = None, smooth: bool = False,
             vertex_colors: Optional[ColorsType] = None, face_colors: Optional[ColorsType] = None,
             compute_normals: bool = True, **kwargs):
        """
        Draws a mesh. Use ``data`` to draw a predetermined shape

        Args:
            vertexes (:class:`np.ndarray <numpy.ndarray>`, optional): ``(Nv, 3)`` array of vertex coordinates. If
                faces is not specified, then this will instead be interpreted as ``(Nf, 3, 3)`` array of coordinates.
            faces: (:class:`np.ndarray <numpy.ndarray>`, optional): ``(Nf, 3)`` array of indexes into the vertex array.
            color: Default face color used if no vertex or face colors  are specified.
            draw_edges (bool): Whether to draw edges. Defaults to ``False``.
            draw_faces (bool): Whether to draw faces. Defaults to ``True``.
            shader (bool): Name of shader program to use when drawing faces. Defaults to ``None``, meaning no shader.
                todo: explain options
            smooth (bool): If ``True``, normal vectors are computed for each vertex and interpolated within each face.
                Defaults to ``False``.
            vertex_colors (:class:`numpy.ndarray <numpy.ndarray>`): Vertex colors. Defaults to ``None``.
            face_colors (:class:`numpy.ndarray <numpy.ndarray>`): Face colors. Defaults to ``None``.
            compute_normals (bool): If ``False``, then computation of normal vectors is disabled. This can provide
                a performance boost for meshes that do not make use of normals.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["vertexes", "faces", "shader", "vertex_colors", "face_colors"],
                                    exclude_args=["self", "kwargs"])

        curve = Mesh()
        curve.set_data(**new_kwargs)
        self.add_curve(curve)
        return curve

    def sphere_mesh(self, radius: float = 1., nrows: int = 20, ncols: int = 20,
                    vertexes: Optional[NDArray] = None, faces: Optional[NDArray] = None,
                    color: ColorType = (1, 1, 1, 0.1), draw_edges: bool = False, draw_faces: bool = True,
                    shader: Optional[str] = None, smooth: bool = False,
                    vertex_colors: Optional[ColorsType] = None, face_colors: Optional[ColorsType] = None,
                    compute_normals: bool = True, **kwargs):
        """
        Draws a mesh. Use ``data`` to draw a predetermined shape

        Args:
            radius (float): Radius of the sphere.
            nrows (int): Number of rows in the mesh. Defaults to ``10``.
            ncols (int): Number of columns in the mesh. Defaults to ``10``.
            vertexes (:class:`np.ndarray <numpy.ndarray>`, optional): ``(Nv, 3)`` array of vertex coordinates. If
                faces is not specified, then this will instead be interpreted as ``(Nf, 3, 3)`` array of coordinates.
            faces: (:class:`np.ndarray <numpy.ndarray>`, optional): ``(Nf, 3)`` array of indexes into the vertex array.
            color: Default face color used if no vertex or face colors  are specified.
            draw_edges (bool): Whether to draw edges. Defaults to ``False``.
            draw_faces (bool): Whether to draw faces. Defaults to ``True``.
            shader (bool): Name of shader program to use when drawing faces. Defaults to ``None``, meaning no shader.
                todo: explain options
            smooth (bool): If ``True``, normal vectors are computed for each vertex and interpolated within each face.
                Defaults to ``False``.
            vertex_colors (:class:`numpy.ndarray <numpy.ndarray>`): Vertex colors. Defaults to ``None``.
            face_colors (:class:`numpy.ndarray <numpy.ndarray>`): Face colors. Defaults to ``None``.
            compute_normals (bool): If ``False``, then computation of normal vectors is disabled. This can provide
                a performance boost for meshes that do not make use of normals.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["vertexes", "faces", "shader", "vertex_colors", "face_colors"],
                                    exclude_args=["self", "kwargs"])

        curve = SphereMesh(radius, nrows, ncols)
        curve.set_data(**new_kwargs)
        self.add_curve(curve)
        return curve

    def cube_mesh(self, side_length: float = 1.,
                  vertexes: Optional[NDArray] = None, faces: Optional[NDArray] = None,
                  color: ColorType = (1, 1, 1, 0.1), draw_edges: bool = False, draw_faces: bool = True,
                  shader: Optional[str] = None, smooth: bool = False,
                  vertex_colors: Optional[ColorsType] = None, face_colors: Optional[ColorsType] = None,
                  compute_normals: bool = True, **kwargs):
        """
        Draws a mesh. Use ``data`` to draw a predetermined shape

        Args:
            side_length (float): Side length of the cube. Defaults to ``1``.
            vertexes (:class:`np.ndarray <numpy.ndarray>`, optional): ``(Nv, 3)`` array of vertex coordinates. If
                faces is not specified, then this will instead be interpreted as ``(Nf, 3, 3)`` array of coordinates.
            faces: (:class:`np.ndarray <numpy.ndarray>`, optional): ``(Nf, 3)`` array of indexes into the vertex array.
            color: Default face color used if no vertex or face colors  are specified.
            draw_edges (bool): Whether to draw edges. Defaults to ``False``.
            draw_faces (bool): Whether to draw faces. Defaults to ``True``.
            shader (bool): Name of shader program to use when drawing faces. Defaults to ``None``, meaning no shader.
                todo: explain options
            smooth (bool): If ``True``, normal vectors are computed for each vertex and interpolated within each face.
                Defaults to ``False``.
            vertex_colors (:class:`numpy.ndarray <numpy.ndarray>`): Vertex colors. Defaults to ``None``.
            face_colors (:class:`numpy.ndarray <numpy.ndarray>`): Face colors. Defaults to ``None``.
            compute_normals (bool): If ``False``, then computation of normal vectors is disabled. This can provide
                a performance boost for meshes that do not make use of normals.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["vertexes", "faces", "shader", "vertex_colors", "face_colors"],
                                    exclude_args=["self", "kwargs"])

        curve = CubeMesh(side_length)
        curve.set_data(**new_kwargs)
        self.add_curve(curve)
        return curve
