#!/usr/bin/env python
"""
svx_output.py
Python script for exporting survex (.svx) file from Inkscape

Copyright (C) 2015, 2020 Patrick B Warren

Email: patrickbwarren@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see
<http://www.gnu.org/licenses/>.
"""

import os
import sys
import inkex

class ExportSurvex(inkex.EffectExtension):

    def add_arguments(self, pars):

        pars.add_argument('--tab', help='Dummy argument')
        pars.add_argument('--directory', default=os.path.expanduser('~'), help='Destination directory')
        pars.add_argument('--file', help='Destination .svx file (with or without extension)')
        pars.add_argument('--ignore', type=inkex.Boolean, help='Ignore file defaults')
        pars.add_argument('--layer', type=inkex.Boolean, help='Restrict export to given layer')
        pars.add_argument('--scale', type=float, default=100.0, help='Length of scale bar (in m)')
        pars.add_argument('--north', type=float, default=0.0, help='Bearing for orientation line (in degrees)')
        pars.add_argument('--tol', type=float, default=0.2, help='Tolerance to equate stations (in m)')
        pars.add_argument('--path-color', type=inkex.Color, default=inkex.Color("red"), help="Path export color")
        pars.add_argument('--orient-color', type=inkex.Color, default=inkex.Color("green"), help="Path export color")
        pars.add_argument('--scale-color', type=inkex.Color, default=inkex.Color("blue"), help="Path export color")
        
    def effect(self):

        sys.stderr.write(f'directory = {self.options.directory}\n')
        sys.stderr.write(f'file = {self.options.file}\n')
        sys.stderr.write(f'ignore = {self.options.ignore}\n')
        sys.stderr.write(f'layer = {self.options.layer}\n')
        sys.stderr.write(f'scale = {self.options.scale}\n')
        sys.stderr.write(f'north = {self.options.north}\n')
        sys.stderr.write(f'tol = {self.options.tol}\n')
        sys.stderr.write(f'path-color = {self.options.path_color.to_rgb()}\n')
        sys.stderr.write(f'orient-color = {self.options.orient_color.to_rgb()}\n')
        sys.stderr.write(f'scale-color = {self.options.scale_color.to_rgb()}\n')
        
        #if not os.path.isdir(self.options.directory):
         #   os.makedirs(self.options.directory)

        #nodes = self.get_layer_nodes(self.options.layer)
        #if nodes is None:
        #    raise inkex.AbortExtension("Slice: '{}' does not exist.".format(self.options.layer))


if __name__ == "__main__":
    ExportSurvex().run()
