# -*- coding: utf-8 -*-
# Copyright 2018-2021 the orix developers
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

import matplotlib.pyplot as plt
import numpy as np


class EulerColorKey:
    def __init__(self, symmetry):
        self.symmetry = symmetry

    def __repr__(self):
        sym = self.symmetry
        max_euler = sym.euler_fundamental_region
        max_euler = np.array_str(max_euler, precision=2, suppress_small=True)
        max_euler = "(" + max_euler.strip("[]") + ")"
        return (
            f"{self.__class__.__name__}, symmetry {sym.name}"
            f"\nMax (phi1, Phi, phi2): {max_euler}"
        )

    def orientation2color(self, orientation):
        return self._euler2color(orientation.in_euler_fundamental_region())

    def plot(self, return_figure=False):
        """Plot the color key.

        Parameters
        ----------
        return_figure : bool, optional
            Whether to return the figure. Default is False.

        Returns
        -------
        figure : matplotlib.figure.Figure
            Color key figure, returned if `return_figure` is True.
        """
        eulers_max = self.symmetry.euler_fundamental_region

        steps = 100
        gradient = np.linspace(0, 1, steps)
        red = np.zeros((steps, 3))
        red[:, 0] = gradient
        green = np.zeros((steps, 3))
        green[:, 1] = gradient
        blue = np.zeros((steps, 3))
        blue[:, 2] = gradient
        gradients = (red, green, blue)

        x_max = np.round(eulers_max).astype(int) - 1
        titles = (r"$\phi_1$", r"$\Phi$", r"$\phi_2$")

        nrows = 3
        fig = plt.figure(figsize=(5, 1.25))
        gs = plt.GridSpec(nrows=nrows, ncols=360)
        for i in range(nrows):
            gradient = gradients[i]
            gradient = np.stack((gradient, gradient))

            x_max_i = x_max[i]
            pad = 0.01 * x_max[0] / x_max_i

            ax = fig.add_subplot(gs[i, :x_max_i])
            ax.imshow(gradient, aspect="auto")
            text_kwargs = dict(transform=ax.transAxes, va="center")
            ax.text(0 - pad, 0.5, titles[i], ha="right", **text_kwargs)
            ax.text(
                1 + pad,
                0.5,
                str(eulers_max[i]) + r"$^{\circ}$",
                ha="left",
                **text_kwargs,
            )
            ax.set_xticks([], [])
            ax.set_yticks([], [])

        if return_figure:
            return fig

    def _euler2color(self, euler):
        max_angles = np.radians(self.symmetry.euler_fundamental_region)
        rgb = euler / max_angles[np.newaxis, :]
        return rgb.clip(0, 1)
