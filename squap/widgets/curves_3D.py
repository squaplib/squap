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


class SurfaceCurve(GLSurfacePlotItem):
    kwarg_mapping = {"c": "color", "colour": "color", "sg": "show_grid", "gc": "grid_color", "gw": "grid_width",
                     "ss": "show_surface", "ga": "grid_antialias", "cn": "compute_normals"}
    shader_map = {"none": None, "balloon": "balloon", "shaded": "shaded", "normal_color": "normalColor",
                  "view_normal_color": "viewNormalColor", "edge_highlight": "edgeHilight"}

    def __init__(self, parent_ax, **kwargs):
        super().__init__(smooth=False, computeNormals=True)

        self.parent_ax = parent_ax
        self.single_color = None
        self.shape = (0, 0)
        self.cmap = None        # plasma is nice
        self.alpha = None
        self.last_azimuth, self.last_elevation = None, None
        self.threshold = 20      # how many degree change should cause a sort_faces call.
        self.opacity = None
        self.smooth = True
        if kwargs.get("cmap") is None and kwargs.get("color") is None:
            kwargs["cmap"] = "plasma"

        parent_ax.cameraChanged.connect(self.resort_faces)

        self.set_data(**kwargs)

    def set_data(self, x: Optional[Iterable] = None, y: Optional[Iterable] = None, z: Optional[Iterable] = None,
                 **kwargs):
        final_kwargs = {}
        new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)

        old_shape = self.shape
        if x is not None:
            final_kwargs["x"] = x
            self.shape = (len(x), self.shape[1])
        if y is not None:
            final_kwargs["y"] = y
            self.shape = (self.shape[0], len(y))
        if z is not None:
            final_kwargs["z"] = z

        if "cmap" in new_kwargs:
            self.cmap = get_cmap(new_kwargs["cmap"])

        if "alpha" in new_kwargs:
            self.alpha = new_kwargs["alpha"]

        # first update color if color, z, or cmap changes.
        if new_kwargs.get("color") is not None:
            self.cmap = None        # if color is given, cmap should not be used anymore
            if is_multiple_colors(new_kwargs["color"]):
                self.single_color = None
                final_kwargs["colors"] = new_kwargs["color"]
            else:
                colors = np.zeros((*self.shape, 4))
                self.single_color = np.array(get_single_color(new_kwargs["color"]).toTuple())/255
                colors[:] = self.single_color
                final_kwargs["colors"] = colors
        elif self.shape != old_shape and self.single_color is not None:
            # if the shape changes, color should change accordingly
            colors = np.zeros((*self.shape, 4))
            colors[:] = self.single_color
            final_kwargs["colors"] = colors
        elif self.cmap is not None:
            if z is not None:
                final_kwargs["colors"] = self.cmap(normalise_arr(z))
            elif "cmap" in new_kwargs:      # if cmap was changed in this set_data
                final_kwargs["colors"] = self.cmap(normalise_arr(self._z))

        # then update the alpha channel if alpha is specified
        if self.alpha is not None and ("colors" in final_kwargs or "alpha" in new_kwargs):
            if "colors" in final_kwargs:
                colors = final_kwargs["colors"]
            elif hasattr(self, "_colors"):
                colors = self._colors
            else:
                colors = None
            if colors is not None:
                if colors.shape[-1] == 3:
                    alpha = np.full(colors.shape[:-1] + (1,), self.alpha, dtype=colors.dtype)
                    colors = np.concatenate([colors, alpha], axis=-1)
                else:
                    if "colors" not in final_kwargs and not self.smooth:    # for smooth, colors is shaped differently
                        colors[:, 3] = self.alpha
                    else:
                        colors[:, :, 3] = self.alpha

                final_kwargs["colors"] = colors

        # then reshape if smooth is False, or if smooth changes and color does not (smooth == False expects color to be
        # shape (Nx*Ny, 4) and smooth == True expects (Nx, Ny, 4)
        if "smooth" in new_kwargs:
            if new_kwargs["smooth"] != self.smooth:
                self.smooth = new_kwargs["smooth"]
                self.opts["smooth"] = self.smooth
                if "colors" not in final_kwargs and hasattr(self, "_colors"):
                    if self.smooth:
                        self._colors.reshape((*self._z.shape, 4))
                    else:
                        old_shape = self._colors.shape
                        self._colors.reshape(old_shape[0]*old_shape[1], 4)

        if "colors" in final_kwargs and not self.smooth:
            final_kwargs["colors"] = final_kwargs["colors"].reshape(-1, 4)

        if "show_surface" in new_kwargs:
            self.opts['drawFaces'] = new_kwargs["show_surface"]
            self.update()

        if "show_grid" in new_kwargs:
            final_kwargs["showGrid"] = new_kwargs["show_grid"]
            if not new_kwargs["show_grid"]:
                self.lineplot.setData(pos=np.empty((0, 3)))
        if "grid_color" in new_kwargs:
            final_kwargs["lineColor"] = get_single_color(new_kwargs["grid_color"])
        if "grid_width" in new_kwargs:
            final_kwargs["lineWidth"] = new_kwargs["grid_width"]
        if "grid_antialias" in new_kwargs:
            final_kwargs["lineAntialias"] = new_kwargs["grid_antialias"]
        if "opacity" in new_kwargs:
            self.setGLOptions(new_kwargs["opacity"])
            self.opacity = new_kwargs["opacity"]
        if "shader" in new_kwargs:
            self.setShader(self.shader_map[new_kwargs["shader"]])
        if "compute_normals" in new_kwargs:
            self.opts["computeNormals"] = new_kwargs["compute_normals"]

        if self.shape != (0, 0):
            self.setData(**final_kwargs)
            if "colors" in final_kwargs and "z" not in final_kwargs:    # eg. meshDataChangedwhen you change cmap while paused
                self.meshDataChanged()

    def resort_faces(self):       # this method was generated with a lot of help from claude
        """
        Whenever the camera angle changes enough and the opacity is set to translucent, the faces are resorted. If this
        is not done, the transparency only renders properly if the face order happens to align with the camera: Faces
        that are drawn behind existing faces do not render.
        """
        camera_params = self.parent_ax.cameraParams()
        azimuth, elevation = camera_params["azimuth"], camera_params["elevation"]
        if (self.last_azimuth is None or abs(self.last_azimuth - azimuth) > self.threshold
            or abs(self.last_elevation - elevation) > self.threshold) and self.opacity == "translucent":

            md = self.opts['meshdata']
            verts = md.vertexes()
            if verts is not None:
                faces = md.faces()
                self.last_azimuth, self.last_elevation = azimuth, elevation

                az, el = np.radians(azimuth), np.radians(elevation)
                center = np.array(camera_params['center'].toTuple())
                dist = camera_params['distance']
                eye = center + dist * np.array([
                    np.cos(el) * np.cos(az),
                    np.cos(el) * np.sin(az),
                    np.sin(el),
                ])

                # faces: (n_tris, 3) vertex indices
                tri_verts = verts[faces]  # (n_tris, 3, 3)
                centroids = tri_verts.mean(axis=1)  # (n_tris, 3)
                dist = np.linalg.norm(centroids - eye, axis=1)
                order = np.argsort(-dist)  # far first

                self._meshdata.setFaces(faces[order])
                self.update()


class Mesh(GLMeshItem):
    kwarg_mapping = {"c": "color", "colour": "color", "de": "draw_edges", "df": "draw_faces", "vc": "vertex_colors",
                     "fc":"face_colors", "cn": "compute_normals"}
    shader_map = {"none": None, "balloon": "balloon", "shaded": "shaded", "normal_color": "normalColor",
                  "view_normal_color": "viewNormalColor", "edge_highlight": "edgeHilight"}

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
            self.setShader(self.shader_map[new_kwargs["shader"]])

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
    def __init__(self, radius: float = 1.0, position: Iterable[float] = (0., 0., 0.), nrows: int = 20, ncols: int = 20, **kwargs):
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
