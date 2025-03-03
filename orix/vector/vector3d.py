# -*- coding: utf-8 -*-
# Copyright 2018-2023 the orix developers
#
# This file is part of orix.
#
# orix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# orix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with orix.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import dask.array as da
from dask.diagnostics import ProgressBar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from orix.base import Object3d


class Vector3d(Object3d):
    """Vector base class.

    Vectors support the following mathematical operations:
        - Unary negation.
        - Addition to other vectors, scalars, numbers, and compatible
          array-like objects.
        - Subtraction to and from the above.
        - Multiplication to scalars, numbers, and compatible array-like
          objects.
        - Division by the same as multiplication. Division by a vector
          is not defined in general.

    Examples
    --------
    >>> from orix.vector import Vector3d
    >>> v = Vector3d((1, 2, 3))
    >>> w = Vector3d(np.array([[1, 0, 0], [0, 1, 1]]))
    >>> w.x
    array([1, 0])
    >>> v.unit
    Vector3d (1,)
    [[0.2673 0.5345 0.8018]]
    >>> -v
    Vector3d (1,)
    [[-1 -2 -3]]
    >>> v + w
    Vector3d (2,)
    [[2 2 3]
     [1 3 4]]
    >>> w - (2, -3)
    Vector3d (2,)
    [[-1 -2 -2]
     [ 3  4  4]]
    >>> 3 * v
    Vector3d (1,)
    [[3 6 9]]
    >>> v / 2
    Vector3d (1,)
    [[0.5 1.  1.5]]
    >>> v / (2, -2)
    Vector3d (2,)
    [[ 0.5  1.   1.5]
     [-0.5 -1.  -1.5]]
    """

    dim = 3

    @property
    def x(self) -> np.ndarray:
        """Return or set the x coordinates.

        Parameters
        ----------
        value : np.ndarray
            The new x coordinates.
        """
        return self.data[..., 0]

    @x.setter
    def x(self, value: np.ndarray):
        """Set the x coordinates."""
        self.data[..., 0] = value

    @property
    def y(self) -> np.ndarray:
        """Return or set the y coordinates.

        Parameters
        ----------
        value : np.ndarray
            The new y coordinates.
        """
        return self.data[..., 1]

    @y.setter
    def y(self, value: np.ndarray):
        """Set the y coordinates."""
        self.data[..., 1] = value

    @property
    def z(self) -> np.ndarray:
        """Return or set the z coordinate.

        Parameters
        ----------
        value : np.ndarray
            The new z coordinate.
        """
        return self.data[..., 2]

    @z.setter
    def z(self, value: np.ndarray):
        """Set the z coordinates."""
        self.data[..., 2] = value

    @property
    def xyz(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return the coordinates as three arrays, useful for
        plotting.
        """
        return self.x, self.y, self.z

    @property
    def _tuples(self) -> Set:
        """Return the set of comparable vectors."""
        s = self.flatten()
        tuples = set([tuple(d) for d in s.data])
        return tuples

    @property
    def perpendicular(self) -> Vector3d:
        """Return the perpendicular vectors."""
        if np.any(self.x == 0) and np.any(self.y == 0):
            if np.any(self.z == 0):
                raise ValueError("No vectors are perpendicular")
            return Vector3d.xvector()
        x = -self.y
        y = self.x
        z = np.zeros_like(x)
        return Vector3d(np.stack((x, y, z), axis=-1))

    @property
    def radial(self) -> np.ndarray:
        """Return the radial spherical coordinate, i.e. the distance
        from a point on the sphere to the origin, according to the
        ISO 31-11 standard :cite:`weisstein2005spherical`.

        Returns
        -------
        radial
            Radial spherical coordinate.
        """
        return np.sqrt(
            self.data[..., 0] ** 2 + self.data[..., 1] ** 2 + self.data[..., 2] ** 2
        )

    @property
    def azimuth(self) -> np.ndarray:
        r"""Azimuth spherical coordinate, i.e. the angle
        :math:`\phi \in [0, 2\pi]` from the positive z-axis to a point
        on the sphere, according to the ISO 31-11 standard
        :cite:`weisstein2005spherical`.

        Returns
        -------
        azimuth
        """
        x, y = self.data[..., 0], self.data[..., 1]
        # avoid rounding errors
        x[np.isclose(x, 0)] = 0
        y[np.isclose(y, 0)] = 0
        azimuth = np.arctan2(y, x)
        azimuth += (azimuth < 0) * 2 * np.pi
        return azimuth

    @property
    def polar(self) -> np.ndarray:
        r"""Polar spherical coordinate, i.e. the angle
        :math:`\theta \in [0, \pi]` from the positive z-axis to a point
        on the sphere, according to the ISO 31-11 standard
        :cite:`weisstein2005spherical`.

        Returns
        -------
        polar
        """
        return np.arccos(self.data[..., 2] / self.radial.data)

    def __neg__(self) -> Vector3d:
        return self.__class__(-self.data)

    def __add__(
        self, other: Union[int, float, List, Tuple, np.ndarray, Vector3d]
    ) -> Vector3d:
        if isinstance(other, Vector3d):
            return self.__class__(self.data + other.data)
        elif isinstance(other, (int, float)):
            return self.__class__(self.data + other)
        elif isinstance(other, (list, tuple)):
            other = np.array(other)

        if isinstance(other, np.ndarray):
            return self.__class__(self.data + other[..., np.newaxis])

        return NotImplemented

    def __radd__(self, other: Union[int, float, List, Tuple, np.ndarray]) -> Vector3d:
        if isinstance(other, (int, float)):
            return self.__class__(other + self.data)
        elif isinstance(other, (list, tuple)):
            other = np.array(other)

        if isinstance(other, np.ndarray):
            return self.__class__(other[..., np.newaxis] + self.data)

        return NotImplemented

    def __sub__(
        self, other: Union[int, float, List, Tuple, np.ndarray, Vector3d]
    ) -> Vector3d:
        if isinstance(other, Vector3d):
            return self.__class__(self.data - other.data)
        elif isinstance(other, (int, float)):
            return self.__class__(self.data - other)
        elif isinstance(other, (list, tuple)):
            other = np.array(other)

        if isinstance(other, np.ndarray):
            return self.__class__(self.data - other[..., np.newaxis])

        return NotImplemented

    def __rsub__(self, other: Union[int, float, List, Tuple, np.ndarray]) -> Vector3d:
        if isinstance(other, (int, float)):
            return self.__class__(other - self.data)
        elif isinstance(other, (list, tuple)):
            other = np.array(other)

        if isinstance(other, np.ndarray):
            return self.__class__(other[..., np.newaxis] - self.data)

        return NotImplemented

    def __mul__(
        self, other: Union[int, float, List, Tuple, np.ndarray, Vector3d]
    ) -> Vector3d:
        if isinstance(other, Vector3d):
            raise ValueError(
                "Multiplying one vector with another is ambiguous. "
                "Try `.dot` or `.cross` instead."
            )
        elif isinstance(other, (int, float)):
            return self.__class__(self.data * other)
        elif isinstance(other, (list, tuple)):
            other = np.array(other)

        if isinstance(other, np.ndarray):
            return self.__class__(self.data * other[..., np.newaxis])

        return NotImplemented

    def __rmul__(self, other: Union[int, float, List, Tuple, np.ndarray]) -> Vector3d:
        if isinstance(other, (int, float)):
            return self.__class__(other * self.data)
        elif isinstance(other, (list, tuple)):
            other = np.array(other)

        if isinstance(other, np.ndarray):
            return self.__class__(other[..., np.newaxis] * self.data)

        return NotImplemented

    def __truediv__(
        self, other: Union[int, float, List, Tuple, np.ndarray, Vector3d]
    ) -> Vector3d:
        if isinstance(other, Vector3d):
            raise ValueError("Dividing vectors is undefined")
        elif isinstance(other, (int, float)):
            return self.__class__(self.data / other)
        elif isinstance(other, (list, tuple)):
            other = np.array(other)

        if isinstance(other, np.ndarray):
            return self.__class__(self.data / other[..., np.newaxis])

        return NotImplemented

    def __rtruediv__(self, other: Any):
        raise ValueError("Division by a vector is undefined")

    def dot(self, other: Vector3d) -> np.ndarray:
        """Return the dot products of the vectors and the other vectors.

        Parameters
        ----------
        other
            Other vectors with a compatible shape.

        Returns
        -------
        dot_products
            Dot products.

        Examples
        --------
        >>> from orix.vector import Vector3d
        >>> v = Vector3d((0, 0, 1.0))
        >>> w = Vector3d(((0, 0, 0.5), (0.4, 0.6, 0)))
        >>> v.dot(w)
        array([0.5, 0. ])
        >>> w.dot(v)
        array([0.5, 0. ])
        """
        if not isinstance(other, Vector3d):
            raise ValueError("{} is not a vector!".format(other))
        return np.sum(self.data * other.data, axis=-1)

    def dot_outer(
        self,
        other: Vector3d,
        lazy: bool = False,
        chunk_size: int = 20,
        progressbar: bool = False,
    ) -> np.ndarray:
        """Return the outer dot products of all vectors and all the
        other vectors.

        Parameters
        ----------
        other
            Compute the outer dot product with these vectors.
        lazy
            Whether to perform the computation lazily with Dask. Default
            is ``False``.
        chunk_size
            Number of orientations per axis to include in each iteration
            of the computation. Default is 20. Only applies when
            ``lazy`` is ``True``.
        progressbar
            Whether to show a progressbar during computation if ``lazy``
            is ``True``. Default is ``True``.

        Returns
        -------
        dot_products
            Dot products.

        Examples
        --------
        >>> from orix.vector import Vector3d
        >>> v = Vector3d(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)))  # shape = (2, )
        >>> w = Vector3d(((0.0, 0.0, 0.5), (0.4, 0.6, 0.0), (0.5, 0.5, 0.5)))  # shape = (3, )
        >>> v.dot_outer(w)
        array([[0.5, 0. , 0.5],
               [0. , 0.4, 0.5]])
        >>> w.dot_outer(v)  # shape = (3, 2)
        array([[0.5, 0. ],
               [0. , 0.4],
               [0.5, 0.5]])
        """
        if lazy:
            dots = np.empty(self.shape + other.shape)
            dp = self._dot_outer_dask(other, chunk_size)
            if progressbar:
                with ProgressBar():
                    da.store(sources=dp, targets=dots)
            else:
                da.store(sources=dp, targets=dots)
        else:
            dots = np.tensordot(self.data, other.data, axes=(-1, -1))
        return dots

    def cross(self, other: Vector3d) -> Vector3d:
        """Return the cross product of a vector with another vector.

        Vectors must have compatible shape for broadcasting to work.

        Returns
        -------
        vec
            The class of ``other`` is preserved.

        Examples
        --------
        >>> from orix.vector import Vector3d
        >>> v = Vector3d(((1, 0, 0), (-1, 0, 0)))
        >>> w = Vector3d((0, 1, 0))
        >>> v.cross(w)
        Vector3d (2,)
        [[ 0  0  1]
         [ 0  0 -1]]
        """
        return other.__class__(np.cross(self.data, other.data))

    @classmethod
    def from_polar(
        cls,
        azimuth: Union[np.ndarray, list, tuple, float],
        polar: Union[np.ndarray, list, tuple, float],
        radial: float = 1.0,
        degrees: bool = False,
    ) -> Vector3d:
        """Initialize from spherical coordinates according to the ISO
        31-11 standard :cite:`weisstein2005spherical`.

        Parameters
        ----------
        azimuth
            Azimuth angle(s) in radians (``degrees=False``) or degrees
            (``degrees=True``).
        polar
            Polar angle(s) in radians (``degrees=False``) or degrees
            (``degrees=True``).
        radial
            Radial distance. Defaults to 1 to produce unit vectors.
        degrees
            If ``True``, the angles are assumed to be in degrees.
            Default is ``False``.

        Returns
        -------
        vec
        """
        azimuth = np.atleast_1d(azimuth)
        polar = np.atleast_1d(polar)
        if degrees:
            azimuth = np.deg2rad(azimuth)
            polar = np.deg2rad(polar)
        sin_polar = np.sin(polar)
        x = np.cos(azimuth) * sin_polar
        y = np.sin(azimuth) * sin_polar
        z = np.cos(polar)
        return radial * cls(np.stack((x, y, z), axis=-1))

    @classmethod
    def zero(cls, shape: Tuple[int] = (1,)) -> Vector3d:
        """Return zero vectors in the specified shape.

        Parameters
        ----------
        shape
            Output vectors' shape.

        Returns
        -------
        vec
            Zero vectors.
        """
        return cls(np.zeros(shape + (cls.dim,)))

    @classmethod
    def xvector(cls) -> Vector3d:
        """Return a unit vector in the x-direction."""
        return cls((1, 0, 0))

    @classmethod
    def yvector(cls) -> Vector3d:
        """Return a unit vector in the y-direction."""
        return cls((0, 1, 0))

    @classmethod
    def zvector(cls) -> Vector3d:
        """Return a unit vector in the z-direction."""
        return cls((0, 0, 1))

    def angle_with(self, other: Vector3d, degrees: bool = False) -> np.ndarray:
        """Return the angles between these vectors in other vectors.

        Vectors must have compatible shapes for broadcasting to work.

        Parameters
        ----------
        other
            Another vector.
        degrees
            If ``True``, the given angles are returned in degrees.
            Default is ``False``.

        Returns
        -------
        angles
            Angles in radians (``degrees=False``)  or degrees
            (``degrees=True``).
        """
        cosines = np.round(self.dot(other) / self.norm / other.norm, 10)
        angles = np.arccos(cosines)
        if degrees:
            angles = np.rad2deg(angles)
        return angles

    def rotate(
        self,
        axis: Union[np.ndarray, Vector3d] = None,
        angle: Union[List[float], float, np.np.ndarray] = 0,
    ) -> Vector3d:
        """Convenience function for rotating this vector.

        Shapes of ``axis`` and ``angle`` must be compatible with shape
        of ``self`` for broadcasting.

        Parameters
        ----------
        axis
            The axis of rotation. Defaults to the z-vector.
        angle
            The angle of rotation, in radians.

        Returns
        -------
        vec
            A new vector with entries rotated.

        Examples
        --------
        >>> from orix.vector import Vector3d
        >>> v = Vector3d.yvector()
        >>> axis = Vector3d((0, 0, 1))
        >>> angles = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi]
        >>> v.rotate(axis=axis, angle=angles)
        Vector3d (5,)
        [[ 0.      1.      0.    ]
         [-0.7071  0.7071  0.    ]
         [-1.      0.      0.    ]
         [-0.7071 -0.7071  0.    ]
         [-0.     -1.      0.    ]]
        """
        # Import here to avoid circular import
        from orix.quaternion import Rotation
        from orix.vector.neo_euler import AxAngle

        axis = Vector3d.zvector() if axis is None else axis
        angle = 0 if angle is None else angle
        q = Rotation.from_neo_euler(AxAngle.from_axes_angles(axis, angle))
        return q * self

    def get_nearest(
        self, x: Vector3d, inclusive: bool = False, tiebreak: bool = None
    ) -> Vector3d:
        """Return the vector in ``x`` with the smallest angle to this
        vector.

        Parameters
        ----------
        x
            Set of vectors in which to find the one with the smallest
            angle to this vector.
        inclusive
            If ``False`` (default) vectors exactly parallel to this will
            not be considered.
        tiebreak
            If multiple vectors are equally close to this one,
            ``tiebreak`` will be used as a secondary comparison. By
            default equal to (0, 0, 1).

        Returns
        -------
        vec
            Vector with the smallest angle to this vector.

        Raises
        ------
        ValueError
            If this is not a single vector.

        Examples
        --------
        >>> from orix.vector import Vector3d
        >>> v1 = Vector3d([1, 0, 0])
        >>> v1.get_nearest(Vector3d([[0.5, 0, 0], [0.6, 0, 0]]))
        Vector3d (1,)
        [[0.6 0.  0. ]]
        """
        assert self.size == 1, "`get_nearest` only works for single vectors."
        tiebreak = Vector3d.zvector() if tiebreak is None else tiebreak
        eps = 1e-9 if inclusive else 0
        cosines = x.dot(self)
        mask = np.logical_and(-1 - eps < cosines, cosines < 1 + eps)
        vec = x[mask]
        if vec.size == 0:
            return Vector3d.empty()
        cosines = cosines[mask]
        verticality = vec.dot(tiebreak)
        order = np.lexsort((cosines, verticality))
        return vec[order[-1]]

    def mean(self) -> Vector3d:
        """Return the mean vector.

        Returns
        -------
        vec
            The mean vector.
        """
        axis = tuple(range(self.ndim))
        return self.__class__(self.data.mean(axis=axis))

    def to_polar(
        self, degrees: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        r"""Return the azimuth :math:`\phi`, polar :math:`\theta`, and
        radial :math:`r` spherical coordinates defined as in the ISO
        31-11 standard :cite:`weisstein2005spherical`.

        Parameters
        ----------
        degrees
            If ``True``, the given angles are returned in degrees.
            Default is ``False``.

        Returns
        -------
        azimuth
            Azimuth angles in radians (``degrees=False``) or degrees
            (``degrees=True``).
        polar
            Polar angles in radians (``degrees=False``) or degrees
            (``degrees=True``).
        radial
            Radial values.
        """
        azimuth = self.azimuth
        polar = self.polar
        if degrees:
            azimuth = np.rad2deg(azimuth)
            polar = np.rad2deg(polar)
        return azimuth, polar, self.radial

    def in_fundamental_sector(self, symmetry: "Symmetry") -> Vector3d:
        """Project vectors to a symmetry's fundamental sector (inverse
        pole figure).

        This projection is taken from MTEX'
        :code:`project2FundamentalRegion`.

        Parameters
        ----------
        symmetry
            Symmetry with a fundamental sector.

        Returns
        -------
        vec
            Vectors within the fundamental sector.

        Examples
        --------
        >>> from orix.quaternion.symmetry import D6h, Oh
        >>> from orix.vector import Vector3d
        >>> v = Vector3d((-1, 1, 0))
        >>> v.in_fundamental_sector(Oh)
        Vector3d (1,)
        [[1. 0. 1.]]
        >>> v.in_fundamental_sector(D6h)
        Vector3d (1,)
        [[1.366 0.366 0.   ]]
        """
        fs = symmetry.fundamental_sector
        v = deepcopy(self)

        center = fs.center
        if center.size == 0:
            return v

        if symmetry.name in ["321", "312", "32", "-4"]:
            idx = v.z < 0
            vv = symmetry[-1] * v[idx]
            if vv.size != 0:
                v[idx] = vv
            rot = symmetry[:3]
        elif symmetry.name == "-3":
            idx = v.z < 0
            vv = symmetry[3] * v[idx]
            if vv.size != 0:
                v[idx] = vv
            rot = symmetry[:3]
        else:
            rot = symmetry

        rotated_centers = rot * center
        closeness = v.dot_outer(rotated_centers).round(12)
        idx_max = np.argmax(closeness, axis=-1)
        v2 = ~rot[idx_max] * v

        # Keep the ones already inside the sector
        mask = v <= fs
        v2[mask] = v[mask]

        return v2

    def get_circle(
        self, opening_angle: Union[float, np.ndarray] = np.pi / 2, steps: int = 100
    ) -> Vector3d:
        r"""Get vectors delineating great or small circle(s) with a
        given ``opening_angle`` about each vector.

        Used for plotting plane traces in stereographic projections.

        Parameters
        ----------
        opening_angle
            Opening angle(s) around the vector(s). Default is
            :math:`\pi/2`, giving a great circle. If an array is passed,
            its size must be equal to the number of vectors.
        steps
            Number of vectors to describe each circle, default is 100.

        Returns
        -------
        circles
            Vectors delineating circles with the ``opening_angle`` about
            the vectors.

        Notes
        -----
        A set of ``steps`` number of vectors equal to each vector is
        rotated twice to obtain a circle: (1) About a perpendicular
        vector to the current vector at ``opening_angle`` and (2) about
        the current vector in a full circle.
        """
        circles = self.zero((self.size, steps))
        full_circle = np.linspace(0, 2 * np.pi, num=steps)
        opening_angles = np.ones(self.size) * opening_angle
        for i, (v, oa) in enumerate(zip(self.flatten(), opening_angles)):
            circles[i] = v.rotate(v.perpendicular, oa).rotate(v, full_circle)
        return circles

    def inverse_pole_density_function(
        self,
        resolution: float = 0.25,
        sigma: float = 5,
        log: bool = False,
        colorbar: bool = True,
        symmetry: Optional["Symmetry"] = None,
        weights: Optional[np.ndarray] = None,
        figure: Optional[Figure] = None,
        hemisphere: Optional[str] = None,
        show_hemisphere_label: Optional[bool] = None,
        grid: Optional[bool] = None,
        grid_resolution: Optional[Tuple[float, float]] = None,
        figure_kwargs: Optional[Dict] = None,
        text_kwargs: Optional[Dict] = None,
        return_figure: bool = False,
        **kwargs: Any,
    ) -> Optional[Figure]:
        """Plot the Inverse Pole Density Function (IPDF) within the
        fundamental sector of a given point group symmetry in the
        stereographic projection.

        The IPDF is calculated in terms of Multiples of Random
        Distribution (MRD), ie. multiples of the expected density if the
        pole distribution was completely random, see
        :cite:`rohrer2004distribution`.

        Parameters
        ----------
        resolution
            The angular resolution of the sampling grid in degrees.
            Default value is 0.25.
        sigma
            The angular resolution of the applied broadening in degrees.
            Default value is 5.
        log
            If ``True`` the log(PDF) is calculated. Default is ``True``.
        colorbar
            If ``True`` a colorbar is shown alongside the IPDF plot.
            Default is ``True``.
        symmetry
            The point group symmetry. Default is ``None``, in which case
            ``C1`` is used.
        weights
            The weights for the individual vectors. Default is ``None``,
            in which case each vector is 1.
        figure
            Which figure to plot onto. Default is ``None``, which
            creates a new figure.
        hemisphere
            Which hemisphere(s) to plot the vectors in, defaults to
            ``None``, which means ``"upper"`` if a new figure is
            created, otherwise adds to the current figure's hemispheres.
            Options are ``"upper"`` and ``"lower"``.
        show_hemisphere_label
            Whether to show hemisphere labels ``"upper"`` or
            ``"lower"``. Default is ``True`` if ``hemisphere`` is
            ``"both"``, otherwise ``False``.
        grid
            Whether to show the azimuth and polar grid. Default is
            whatever ``axes.grid`` is set to in
            :obj:`matplotlib.rcParams`.
        grid_resolution
            Azimuth and polar grid resolution in degrees, as a tuple.
            Default is whatever is default in
            :class:`~orix.plot.StereographicPlot.stereographic_grid`.
        figure_kwargs
            Dictionary of keyword arguments passed to
            :func:`matplotlib.pyplot.subplots`.
        text_kwargs
            Dictionary of keyword arguments passed to
            :meth:`~orix.plot.StereographicPlot.text`, which passes
            these on to :meth:`matplotlib.axes.Axes.text`.
        return_figure
            Whether to return the figure (default is ``False``).
        **kwargs
            Keyword arguments passed to
            :meth:`matplotlib.axes.Axes.pcolormesh`.

        Returns
        -------
        fig
            The created figure, returned if ``return_figure=True``.

        See Also
        --------
        orix.measure.pole_density_function
        orix.plot.InversePoleFigurePlot.pole_density_function
        orix.plot.StereographicPlot.pole_density_function
        """
        if hemisphere is None:
            hemisphere = "upper"
        if hemisphere not in ("upper", "lower", "both"):
            raise ValueError('Hemisphere must be either "upper", "lower", or "both".')

        # computation done in spherical coordinates
        azimuth, polar, _ = self.unit.to_polar()

        (
            fig,
            axes,
            hemisphere,
            show_hemisphere_label,
            grid,
            grid_resolution,
            text_kwargs,
            axes_labels,
        ) = self._setup_plot(
            projection="ipf",
            figure=figure,
            hemisphere=hemisphere,
            show_hemisphere_label=show_hemisphere_label,
            symmetry=symmetry,
            grid=grid,
            grid_resolution=grid_resolution,
            figure_kwargs=figure_kwargs,
            text_kwargs=text_kwargs,
        )

        for i, ax in enumerate(axes):
            # setup plot
            ax.hemisphere = hemisphere[i]
            ax.stereographic_grid(grid[i], grid_resolution[0], grid_resolution[1])
            ax._stereographic_grid = grid[i]
            if show_hemisphere_label:
                ax.show_hemisphere_label()

            ax.pole_density_function(
                azimuth,
                polar,
                resolution=resolution,
                sigma=sigma,
                log=log,
                colorbar=colorbar,
                weights=weights,
                **kwargs,
            )

        if return_figure:
            return fig

    def pole_density_function(
        self,
        resolution: float = 1,
        sigma: float = 5,
        log: bool = False,
        colorbar: bool = True,
        weights: Optional[np.ndarray] = None,
        figure: Optional[Figure] = None,
        axes_labels: Optional[List[str]] = None,
        hemisphere: Optional[str] = None,
        show_hemisphere_label: Optional[bool] = None,
        grid: Optional[bool] = None,
        grid_resolution: Optional[Tuple[float, float]] = None,
        figure_kwargs: Optional[Dict] = None,
        text_kwargs: Optional[Dict] = None,
        return_figure: bool = False,
        **kwargs: Any,
    ) -> Optional[Figure]:
        """Plot the Pole Density Function (PDF) on a given hemisphere
        in the stereographic projection.

        The PDF is calculated in terms of Multiples of Random
        Distribution (MRD), ie. multiples of the expected density if the
        pole distribution was completely random, see
        :cite:`rohrer2004distribution`.

        Parameters
        ----------
        resolution
            The angular resolution of the sampling grid in degrees.
            Default value is 1.
        sigma
            The angular resolution of the applied broadening in degrees.
            Default value is 5.
        log
            If ``True`` the log(PDF) is calculated. Default is ``True``.
        colorbar
            If ``True`` a colorbar is shown alongside the PDF plot.
            Default is ``True``.
        weights
            The weights for the individual vectors. Default is ``None``,
            in which case each vector is 1.
        figure
            Which figure to plot onto. Default is ``None``, which
            creates a new figure.
        axes_labels
            Reference frame axes labels, defaults to
            ``[None, None, None]``.
        hemisphere
            Which hemisphere(s) to plot the vectors in, defaults to
            ``None``, which means ``"upper"`` if a new figure is
            created, otherwise adds to the current figure's hemispheres.
            Options are ``"upper"`` and ``"lower"``.
        show_hemisphere_label
            Whether to show hemisphere labels ``"upper"`` or
            ``"lower"``. Default is ``True`` if ``hemisphere`` is
            ``"both"``, otherwise ``False``.
        grid
            Whether to show the azimuth and polar grid. Default is
            whatever ``axes.grid`` is set to in
            :obj:`matplotlib.rcParams`.
        grid_resolution
            Azimuth and polar grid resolution in degrees, as a tuple.
            Default is whatever is default in
            :class:`~orix.plot.StereographicPlot.stereographic_grid`.
        figure_kwargs
            Dictionary of keyword arguments passed to
            :func:`matplotlib.pyplot.subplots`.
        text_kwargs
            Dictionary of keyword arguments passed to
            :meth:`~orix.plot.StereographicPlot.text`, which passes
            these on to :meth:`matplotlib.axes.Axes.text`.
        return_figure
            Whether to return the figure (default is ``False``).
        **kwargs
            Keyword arguments passed to
            :meth:`matplotlib.axes.Axes.pcolormesh`.

        Returns
        -------
        fig
            The created figure, returned if ``return_figure=True``.

        See Also
        --------
        orix.measure.pole_density_function
        orix.plot.InversePoleFigurePlot.pole_density_function
        orix.plot.StereographicPlot.pole_density_function
        """
        if hemisphere is None:
            hemisphere = "upper"
        if hemisphere not in ("upper", "lower", "both"):
            raise ValueError('Hemisphere must be either "upper", "lower", or "both".')

        # computation done in spherical coordinates
        azimuth, polar, _ = self.to_polar()

        (
            fig,
            axes,
            hemisphere,
            show_hemisphere_label,
            grid,
            grid_resolution,
            text_kwargs,
            axes_labels,
        ) = self._setup_plot(
            projection="stereographic",
            figure=figure,
            hemisphere=hemisphere,
            show_hemisphere_label=show_hemisphere_label,
            grid=grid,
            grid_resolution=grid_resolution,
            figure_kwargs=figure_kwargs,
            text_kwargs=text_kwargs,
            axes_labels=axes_labels,
        )

        for i, ax in enumerate(axes):
            # setup plot
            ax.hemisphere = hemisphere[i]
            ax.stereographic_grid(grid[i], grid_resolution[0], grid_resolution[1])
            ax._stereographic_grid = grid[i]
            ax.set_labels(*axes_labels)
            if show_hemisphere_label:
                ax.show_hemisphere_label()

            ax.pole_density_function(
                azimuth,
                polar,
                resolution=resolution,
                sigma=sigma,
                log=log,
                colorbar=colorbar,
                weights=weights,
                **kwargs,
            )

        if return_figure:
            return fig

    def scatter(
        self,
        projection: str = "stereographic",
        figure: Optional[Figure] = None,
        axes_labels: Optional[List[str]] = None,
        vector_labels: Optional[List[str]] = None,
        hemisphere: Optional[str] = None,
        reproject: bool = False,
        show_hemisphere_label: Optional[bool] = None,
        grid: Optional[bool] = None,
        grid_resolution: Optional[Tuple[float, float]] = None,
        figure_kwargs: Optional[Dict] = None,
        reproject_scatter_kwargs: Optional[Dict] = None,
        text_kwargs: Optional[Dict] = None,
        return_figure: bool = False,
        **kwargs: Any,
    ) -> Optional[Figure]:
        """Plot vectors in the stereographic projection.

        Parameters
        ----------
        projection
            Which projection to use. The default is ``"stereographic"``,
            the only current option.
        figure
            Which figure to plot onto. Default is ``None``, which
            creates a new figure.
        axes_labels
            Reference frame axes labels, defaults to
            ``[None, None, None]``.
        vector_labels
            Vector text labels, which by default are not added.
        hemisphere
            Which hemisphere(s) to plot the vectors in, defaults to
            ``None``, which means ``"upper"`` if a new figure is
            created, otherwise adds to the current figure's hemispheres.
            Options are ``"upper"``, ``"lower"``, and ``"both"``, which
            plots two projections side by side.
        reproject
            Whether to reproject vectors onto the chosen hemisphere.
            Reprojection is achieved by reflection of the vectors
            located on the opposite hemisphere in the projection plane.
            Ignored if ``hemisphere`` is ``"both"``. Default is
            ``False``.
        show_hemisphere_label
            Whether to show hemisphere labels ``"upper"`` or
            ``"lower"``. Default is ``True`` if ``hemisphere`` is
            ``"both"``, otherwise ``False``.
        grid
            Whether to show the azimuth and polar grid. Default is
            whatever ``axes.grid`` is set to in
            :obj:`matplotlib.rcParams`.
        grid_resolution
            Azimuth and polar grid resolution in degrees, as a tuple.
            Default is whatever is default in
            :class:`~orix.plot.StereographicPlot.stereographic_grid`.
        figure_kwargs
            Dictionary of keyword arguments passed to
            :func:`matplotlib.pyplot.subplots`.
        reproject_scatter_kwargs
            Dictionary of keyword arguments for the reprojected scatter
            points which is passed to
            :meth:`~orix.plot.StereographicPlot.scatter`, which passes
            these on to :meth:`matplotlib.axes.Axes.scatter`. The
            default marker style for reprojected vectors is ``"+"``.
            Values used for vector(s) on the visible hemisphere are used
            unless another value is passed here.
        text_kwargs
            Dictionary of keyword arguments passed to
            :meth:`~orix.plot.StereographicPlot.text`, which passes
            these on to :meth:`matplotlib.axes.Axes.text`.
        return_figure
            Whether to return the figure (default is ``False``).
        **kwargs
            Keyword arguments passed to
            :meth:`~orix.plot.StereographicPlot.scatter`, which passes
            these on to :meth:`matplotlib.axes.Axes.scatter`.

        Returns
        -------
        fig
            The created figure, returned if ``return_figure=True``.

        Notes
        -----
        This is a somewhat customizable convenience method which creates
        a figure with axes using :class:`~orix.plot.StereographicPlot`,
        however, it is meant for quick plotting and prototyping. This
        figure and the axes can also be created using Matplotlib
        directly, which is more customizable.

        See Also
        --------
        orix.plot.StereographicPlot
        """
        if hemisphere is not None and hemisphere.lower() == "both":
            reproject = False
        if reproject:
            # setup reproject scatter plotting args
            if reproject_scatter_kwargs is None:
                reproject_scatter_kwargs = {}
            reproject_scatter_kwargs.setdefault("marker", "+")
            # unless otherwise defined, copy normal scatter kwargs
            for k, v in kwargs.items():
                if k not in reproject_scatter_kwargs.keys():
                    reproject_scatter_kwargs[k] = v
            v_reprojected = deepcopy(self)
            v_reprojected.z = -v_reprojected.z

        (
            fig,
            axes,
            hemisphere,
            show_hemisphere_label,
            grid,
            grid_resolution,
            text_kwargs,
            axes_labels,
        ) = self._setup_plot(
            projection=projection,
            figure=figure,
            hemisphere=hemisphere,
            show_hemisphere_label=show_hemisphere_label,
            grid=grid,
            grid_resolution=grid_resolution,
            figure_kwargs=figure_kwargs,
            text_kwargs=text_kwargs,
            axes_labels=axes_labels,
        )

        # Use methods of the StereographicPlot class
        for i, ax in enumerate(axes):  # Assumes a maximum of two axes
            ax.hemisphere = hemisphere[i]
            ax.scatter(self, **kwargs)
            if reproject:
                ax.scatter(v_reprojected, **reproject_scatter_kwargs)
            ax.stereographic_grid(grid[i], grid_resolution[0], grid_resolution[1])
            ax._stereographic_grid = grid[i]
            ax.set_labels(*axes_labels)
            if show_hemisphere_label:
                ax.show_hemisphere_label()
            if vector_labels is not None:
                for vi, li in zip(self, vector_labels):
                    ax.text(vi, s=li, **text_kwargs)

        if return_figure:
            return fig

    def draw_circle(
        self,
        projection: str = "stereographic",
        figure: Optional[Figure] = None,
        opening_angle: Union[float, np.ndarray] = np.pi / 2,
        steps: int = 100,
        reproject: bool = False,
        axes_labels: Optional[List[str]] = None,
        hemisphere: Optional[str] = None,
        show_hemisphere_label: Optional[bool] = None,
        grid: Optional[bool] = None,
        grid_resolution: Optional[Tuple[float, float]] = None,
        figure_kwargs: Optional[Dict] = None,
        reproject_plot_kwargs: Optional[Dict] = None,
        return_figure: bool = False,
        **kwargs: Any,
    ) -> Optional[Figure]:
        r"""Draw great or small circles with a given ``opening_angle``
        to to the vectors in the stereographic projection.

        A vector must be present in the current hemisphere for its
        circle to be drawn.

        Parameters
        ----------
        projection
            Which projection to use. The default is ``"stereographic"``,
            the only current option.
        figure
            Which figure to plot onto. Default is ``None``, which
            creates a new figure.
        opening_angle
            Opening angle(s) around the vector(s). Default is
            :math:`\pi/2`, giving a great circle. If an array is passed,
            its size must be equal to the number of vectors.
        steps
            Number of vectors to describe each circle, default is 100.
        reproject
            Whether to reproject parts of the circle(s) visible on the
            other hemisphere. Reprojection is achieved by reflection of
            the circle(s) parts located on the other hemisphere in the
            projection plane. Ignored if hemisphere is ``"both"``.
            Default is ``False``.
        axes_labels
            Reference frame axes labels, defaults to
            ``[None, None, None]``.
        hemisphere
            Which hemisphere(s) to plot the vectors in, defaults to
            ``None``, which means ``"upper"`` if a new figure is
            created, otherwise adds to the current figure's hemispheres.
            Options are ``"upper"``, ``"lower"``, and ``"both"``, which
            plots two projections side by side.
        show_hemisphere_label
            Whether to show hemisphere labels ``"upper"`` or
            ``"lower"``. Default is ``True`` if ``hemisphere`` is
            ``"both"``, otherwise ``False``.
        grid
            Whether to show the azimuth and polar grid. Default is
            whatever ``axes.grid`` is set to in
            :obj:`matplotlib.rcParams`.
        grid_resolution
            Azimuth and polar grid resolution in degrees, as a tuple.
            Default is whatever is default in
            :class:`~orix.plot.StereographicPlot.stereographic_grid`.
        figure_kwargs
            Dictionary of keyword arguments passed to
            :func:`matplotlib.pyplot.subplots`.
        reproject_plot_kwargs
            Keyword arguments passed to
            :meth:`matplotlib.axes.Axes.plot` to alter the appearance of
            parts of the circle(s) visible on the other hemisphere if
            ``reproject=True``. These lines are dashed by default.
            Values used for circle(s) on the current hemisphere are used
            unless values are passed here.
        return_figure
            Whether to return the figure (default is ``False``).
        **kwargs
            Keyword arguments passed to
            :meth:`matplotlib.axes.Axes.plot` to alter the circles'
            appearance.

        Returns
        -------
        fig
            The created figure, returned if ``return_figure=True``.

        Notes
        -----
        This is a somewhat customizable convenience method which creates
        a figure with axes using :class:`~orix.plot.StereographicPlot`,
        however, it is meant for quick plotting and prototyping. This
        figure and the axes can also be created using Matplotlib
        directly, which is more customizable.

        See Also
        --------
        orix.plot.StereographicPlot
        orix.vector.Vector3d.get_circle
        """
        if hemisphere is not None and hemisphere.lower() == "both":
            reproject = False
        if reproject:
            if reproject_plot_kwargs is None:
                reproject_plot_kwargs = {}
            reproject_plot_kwargs.setdefault("linestyle", "--")
            for k, v in kwargs.items():
                if k not in reproject_plot_kwargs.keys() and k != "color":
                    reproject_plot_kwargs[k] = v

        (
            fig,
            axes,
            hemisphere,
            show_hemisphere_label,
            grid,
            grid_resolution,
            _,
            axes_labels,
        ) = self._setup_plot(
            projection=projection,
            figure=figure,
            hemisphere=hemisphere,
            show_hemisphere_label=show_hemisphere_label,
            grid=grid,
            grid_resolution=grid_resolution,
            figure_kwargs=figure_kwargs,
            axes_labels=axes_labels,
        )

        # Use methods of the StereographicPlot class
        for i, ax in enumerate(axes):  # Assumes a maximum of two axes
            ax.hemisphere = hemisphere[i]
            ax.draw_circle(
                self,
                opening_angle=opening_angle,
                steps=steps,
                reproject=reproject,
                reproject_plot_kwargs=reproject_plot_kwargs,
                **kwargs,
            )
            ax.stereographic_grid(grid[i], grid_resolution[0], grid_resolution[1])
            ax._stereographic_grid = grid[i]
            ax.set_labels(*axes_labels)
            if show_hemisphere_label:
                ax.show_hemisphere_label()

        if return_figure:
            return fig

    @staticmethod
    def _setup_plot(
        projection: str = "stereographic",
        figure: Optional[Figure] = None,
        hemisphere: Optional[str] = None,
        show_hemisphere_label: Optional[bool] = None,
        symmetry: Optional["Symmetry"] = None,
        grid: Optional[bool] = None,
        grid_resolution: Optional[Tuple[float, float]] = None,
        figure_kwargs: Optional[Dict] = None,
        text_kwargs: Optional[Dict] = None,
        axes_labels: Optional[List[str]] = None,
    ):
        """Set up a stereographic projection plot.

        Parameters
        ----------
        projection
            Which projection to use. Available projections are ``"ipf"``
            and ``"stereographic"``. If projection is ``"ipf"`` then
            ``symmetry`` must also be defined. The default is
            ``"stereographic"``.
        figure
            Which figure to plot onto. Default is ``None``, which
            creates a new figure.
        hemisphere
            Which hemisphere(s) to plot the vectors in, defaults to
            ``None``, which means ``"upper"`` if a new figure is
            created, otherwise adds to the current figure's hemispheres.
            Options are ``"upper"``, ``"lower"``, and ``"both"``, which
            plots two projections side by side.
        show_hemisphere_label
            Whether to show hemisphere labels ``"upper"`` or
            ``"lower"``. Default is ``True`` if ``hemisphere`` is
            ``"both"``, otherwise ``False``.
        symmetry
            The point group symmetry. Required if ``projection="ipf"``.
        grid
            Whether to show the azimuth and polar grid. Default is
            whatever ``axes.grid`` is set to in
            :obj:`matplotlib.rcParams`.
        grid_resolution
            Azimuth and polar grid resolution in degrees, as a tuple.
            Default is whatever is default in
            :class:`~orix.plot.StereographicPlot.stereographic_grid`.
        figure_kwargs
            Dictionary of keyword arguments passed to
            :func:`matplotlib.pyplot.subplots`.
        text_kwargs
            Dictionary of keyword arguments passed to
            :meth:`~orix.plot.StereographicPlot.text`.
        axes_labels
            List of axes labels, passed to
            :meth:`orix.plot.StereographicPlot.set_labels`.
            Default is ``None``.

        Returns
        -------
        figure
        axes
        hemisphere
        show_hemisphere_label
        grid
        grid_resolution
        text_kwargs
        axes_labels
        """
        projection = projection.lower()

        if projection not in {"ipf", "stereographic"}:
            raise NotImplementedError(
                f'Projection "{projection}" is unsupported. '
                + 'The currently supported projections are "ipf" and "stereographic".'
            )
        if projection == "ipf":
            hemisphere = "upper"

        import orix.plot.stereographic_plot

        if figure is not None:
            axes = figure.axes
            hemisphere = "both" if len(axes) == 2 else axes[0].hemisphere

        # Which hemisphere(s) to plot
        ncols = 1
        hemispheres = ("upper", "lower")
        if hemisphere is None:
            hemisphere = "upper"
        if hemisphere.lower() in hemispheres:
            hemisphere = (hemisphere,)
        elif hemisphere == "both":
            ncols = 2
            hemisphere = hemispheres
            if show_hemisphere_label in [True, None]:
                show_hemisphere_label = True

        # Create new figure and axis/axes
        subplot_kw = dict(projection=projection)
        if projection == "ipf":
            subplot_kw["symmetry"] = symmetry

        if figure is None:
            if figure_kwargs is None:
                figure_kwargs = dict()
            figure, axes = plt.subplots(
                ncols=ncols, subplot_kw=subplot_kw, **figure_kwargs
            )

        # Make axes iterable
        axes = [axes] if not hasattr(axes, "__iter__") else axes

        if show_hemisphere_label is None:
            show_hemisphere_label = False

        # Whether to plot a grid, and with which resolution
        if grid is None:
            grid = [a._stereographic_grid for a in axes]
            if all(g is None for g in grid):
                grid = [plt.rcParams["axes.grid"]] * ncols
        else:
            grid = [grid] * ncols
        if grid_resolution is None:
            grid_resolution = [None] * 2

        if text_kwargs is None:
            text_kwargs = dict()

        new_axes_labels = deepcopy(axes_labels)
        if new_axes_labels is None:
            new_axes_labels = [None, None, None]
        elif len(new_axes_labels) != 3:
            new_axes_labels += [None] * (3 - len(new_axes_labels))

        return (
            figure,
            axes,
            hemisphere,
            show_hemisphere_label,
            grid,
            grid_resolution,
            text_kwargs,
            new_axes_labels,
        )

    def _dot_outer_dask(self, other: Vector3d, chunk_size: int = 20) -> da.Array:
        """Compute the lazy dot product between this vector and another."""
        ndim1 = self.ndim
        ndim2 = other.ndim

        # Set chunk sizes
        chunks1 = (chunk_size,) * ndim1 + (-1,)
        chunks2 = (chunk_size,) * ndim2 + (-1,)

        v1 = da.from_array(self.data, chunks=chunks1)
        v2 = da.from_array(other.data, chunks=chunks2)

        return da.tensordot(v1, v2, axes=(v1.ndim - 1, v2.ndim - 1))
