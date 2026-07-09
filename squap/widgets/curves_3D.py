from pyqtgraph.opengl import GLScatterPlotItem, GLMeshItem, MeshData
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


class LineCurve3D(GLLinePlotItem):
    kwarg_mapping = {"c": "color", "colour": "color", "data": "pos", "w": "width"}

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
            color (:ref:`ColorsType`): Changes the color of the line. See :ref:`ColorsType`
                for allowed values.
            width (int): float specifying line width.
            antialias (bool): Enables smooth line drawing. Defaults to ``False``.
            connect (str): Can be one of the following options:

                - ``"all"``: Connects all points.
                - ``"pairs"``: Generates lines between every other point.

                Defaults to ``"all"``.

        """
        new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)

        if "color" in new_kwargs:
            color = new_kwargs["color"]
            if is_multiple_colors(color):
                color = [get_single_color(col_i) for col_i in color]
            else:
                color = get_single_color(color)
            new_kwargs["color"] = color

        if "connect" in new_kwargs:
            if new_kwargs["connect"] == "all":
                new_kwargs["mode"] = "line_strip"
            elif new_kwargs["connect"] == "pairs":
                new_kwargs["mode"] = "lines"
            else:
                ValueError(f'The option connect={new_kwargs["connect"]} is not allowed.')

            del new_kwargs["connect"]

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


class Mesh(GLMeshItem):
    kwarg_mapping = {"c": "color", "colour": "color", }

    def __init__(self, **kwargs):
        self.mesh_data = MeshData()
        super().__init__(meshdata=self.mesh_data)

    def set_data(self, **kwargs):
        """
        Sets the data of the mesh item after it has been created. Meshes are mostly useful to add some general 3D shapes
        to the view.

        Keyword Args:
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
        new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)

        if "color" in new_kwargs:
            self.setColor(get_single_color(new_kwargs["color"]))

        if "shader" in new_kwargs:
            self.setShader(new_kwargs["shader"])

        for keyword, optkwarg in {"smooth": "smooth", "draw_edges": "drawEdges", "draw_faces": "drawFaces",
                                  "compute_normals": "computeNormals"}.items():
            if keyword in new_kwargs:
                self.opts[optkwarg] = new_kwargs[keyword]

        if "vertexes" in new_kwargs:
            self.mesh_data.setVertexes(new_kwargs["vertexes"])

        if "faces" in new_kwargs:
            self.mesh_data.setFaces(new_kwargs["faces"])

        if "vertex_colors" in new_kwargs:
            self.mesh_data.setVertexColors(new_kwargs["vertex_colors"])

        if "face_colors" in new_kwargs:
            self.mesh_data.setFaceColors(new_kwargs["face_colors"])


class SphereMesh(Mesh):
    def __init__(self, radius=1.0, nrows=20, ncols=20, position=(0., 0., 0.), **kwargs):
        super().__init__(**kwargs)
        self.sphere_data = {"rows": nrows, "cols": ncols, "radius": radius}
        self.position = np.array(position)
        self.mesh_data = MeshData.sphere(**self.sphere_data)
        self.translate(*position)

        self.setMeshData(meshdata=self.mesh_data)

    def set_data(self, **kwargs):
        super().set_data(**kwargs)
        if kwargs:
            if "radius" in kwargs:
                self.sphere_data["radius"] = kwargs["radius"]

            if "nrows" in kwargs:
                self.sphere_data["rows"] = kwargs["nrows"]

            if "ncols" in kwargs:
                self.sphere_data["cols"] = kwargs["ncols"]

            if "position" in kwargs:
                new_pos = np.array(kwargs["position"])
                dif = new_pos - self.position
                self.translate(*dif)
                self.position = new_pos

            self.mesh_data = MeshData.sphere(**self.sphere_data)
            self.setMeshData(meshdata=self.mesh_data)

        super().set_data(**kwargs)


class CubeMesh(Mesh):
    def __init__(self, side_length: float | Iterable[float] = 1., position: Iterable[float] = (0, 0, 0), **kwargs):
        super().__init__(**kwargs)
        self.verts = np.array([
            [0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0],
            [1, 1, 0], [1, 1, 1], [1, 0, 1], [1, 0, 0],
        ])-1/2

        self.faces = np.array([
            [0, 1, 2], [0, 2, 3], [2, 3, 4], [2, 4, 5],
            [4, 5, 6], [4, 6, 7], [6, 7, 0], [6, 0, 1],
            [0, 3, 4], [0, 4, 7], [1, 2, 5], [1, 5, 6],
        ])

        self.side_length = side_length
        self.position = position

        self.set_data(side_length)

    def set_data(self, *args, **kwargs):
        if args:
            if len(args) >= 1:
                self.side_length = args[0]
            if len(args) >= 2:
                self.position = args[1]
        if kwargs:
            if "side_length" in kwargs:
                self.side_length = kwargs["side_length"]
            if "position" in kwargs:
                self.position = kwargs["position"]

        self.mesh_data = MeshData(vertexes=self.verts*self.side_length + self.position, faces=self.faces)
        self.setMeshData(meshdata=self.mesh_data)
        # super().set_data(**kwargs)
