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
from time import strftime
from itertools import combinations
from math import sqrt, atan2, degrees

class ExportSurvex(inkex.EffectExtension):

    def sprintd(self, b):
        "Takes a bearing and returns it as string in 000 format"
        while b < 0: b += 360
        b = int(b + 0.5)
        while b >= 360: b -= 360
        return '%03i' % b

    # need to catch horizontal and vertical steps here

    def distance(self, p0, p1):
        "The distance between two points"
        x0, y0, x1, y1 = *p0.args, *p1.args # '*' flattens the nested list
        dx, dy = x1 - x0, y1 - y0
        dl = sqrt(dx*dx + dy*dy)
        return dl, dx, dy

    def first_step(self, line):
        "The distance between the first two points in a line"
        return self.distance(line[0], line[1])

    def add_arguments(self, pars):

        pars.add_argument('--tab', help='Dummy argument')
        pars.add_argument('--directory', default=os.path.expanduser('~'), help='Destination directory')
        pars.add_argument('--file', help='Destination .svx file (with or without extension)')
        pars.add_argument('--option', help='File name defaults')
        pars.add_argument('--layer', type=inkex.Boolean, help='Restrict export to current layer')
        pars.add_argument('--scale', type=float, default=100.0, help='Length of scale bar (in m)')
        pars.add_argument('--north', type=float, default=0.0, help='Bearing for orientation line (in degrees)')
        pars.add_argument('--tol', type=float, default=0.2, help='Tolerance to equate stations (in m)')
        pars.add_argument('--path-color', type=inkex.Color, default=inkex.Color("red"), help="Path export color")
        pars.add_argument('--orient-color', type=inkex.Color, default=inkex.Color("green"), help="Path export color")
        pars.add_argument('--scale-color', type=inkex.Color, default=inkex.Color("blue"), help="Path export color")
        pars.add_argument('--dump', type=inkex.Boolean, help='dump information')
        
    def effect(self):

        if not os.path.isdir(self.options.directory):
            raise inkex.AbortExtension('The specified directory does not exist')

        # determine the image file name if there is one
        
        el = self.svg.find('.//svg:image', namespaces=inkex.NSS)
        s = '{%s}absref' % inkex.NSS[u'sodipodi']
        img_file = os.path.split(el.attrib[s])[1] if el is not None and s in el.attrib else None

        # get the name of the currently selected layer
        
        el = self.svg.get_current_layer()
        s = '{%s}label' % inkex.NSS[u'inkscape']
        current_layer = el.attrib[s] if el is not None and s in el.attrib else None

        # tfigure out the name of the .svx file
        
        if self.options.option == 'specified':
            file_name = self.options.file
        elif self.options.option == 'document':
            file_name = self.svg.name
        elif self.options.option == 'image':
            file_name = img_file
        elif self.options.option == 'layer':
            if current_layer is None:
                raise inkex.AbortExtension('No layer selected for setting file name')
            file_name = current_layer

        if file_name is None:
            raise inkex.AbortExtension('No file name specified')

        svx_file = os.path.splitext(file_name)[0] + '.svx'

        # find all the polylines in the drawing as a list of dicts

        poly_lines = []

        for path in self.svg.findall('.//svg:g/svg:path', namespaces=inkex.NSS):
            stroke = dict(inkex.Style.parse_str(path.attrib['style']))['stroke']
            layer = path.getparent().attrib['{%s}label' % inkex.NSS[u'inkscape']]
            poly_lines.append({'path': path.path.to_absolute(), 'id': path.attrib['id'],
                               'stroke': stroke, 'layer': layer})

        # Find the scale bar line and calculate the scale factor

        color = str(self.options.scale_color.to_rgb())
        subset = list(filter(lambda el: el['stroke'] == color, poly_lines))
        if not subset:
            raise inkex.AbortExtension('No scale bar found (check settings in color tabs)')
        #sys.stderr.write(f'{subset[0]}\n')
        scale_len, _, _ = self.first_step(subset[0]['path'])
        scale_fac = self.options.scale / scale_len

        # Find the orientation line and construct the unit vector (nx, ny)
        # to point along N, and the unit (ex, ey) to point along E.

        color = str(self.options.orient_color.to_rgb())
        subset = list(filter(lambda el: el['stroke'] == color, poly_lines))
        if not subset:
            raise inkex.AbortExtension('No orientation line found (check settings in color tabs)')
        dl, dx, dy = self.first_step(subset[0]['path'])
        nx, ny = dx/dl, dy/dl
        ex, ey = -ny, nx

        # Find the exportable (poly)lines, restricted to selected layer if desired
        
        color = str(self.options.path_color.to_rgb())
        poly_lines = list(filter(lambda el: el['stroke'] == color, poly_lines))
        if self.options.layer:
            if current_layer is None:
                raise inkex.AbortExtension('No layer selected to filter on')
            poly_lines = list(filter(lambda el: el['layer'] == current_layer, poly_lines))
        if not poly_lines:
            raise inkex.AbortExtension('No exportable lines found (check settings in color tabs and layer selection)')

        # Now build the survex traverses.  Keep track of stations and
        # absolute positions to identify equates and exports.

        # Stations is a list of dicts of (station_id, pos, traverse_name)
        # Traverses is a list of dicts of (traverse_name, legs), where
        # Legs is a list of dicts of (from_id, to_id, tape, compass)

        stations = []
        traverses = []

        for line in poly_lines:
            legs = []
            for i, pos in enumerate(line['path']):
                stations.append({'traverse': line['id'], 'id': str(i), 'pos': pos})
                if i:
                    dl, dx, dy = self.distance(prev_pos, pos)
                    tape = scale_fac * dl
                    compass = self.options.north + degrees(atan2(ex*dx+ey*dy, nx*dx+ny*dy))
                    legs.append({'from': str(i-1), 'to': str(i), 'tape': tape, 'compass': compass})
                prev_pos = pos
            traverses.append({'id': line['id'], 'legs': legs})

        ntraverse = len(traverses)
        nstation = len(stations)
        
        # Identify the equates.  This is an O(n^2) pairwise comparison
        # and more efficient methods are available but n should not
        # get too large: for a large project it almost always bound to
        # be a good idea to break the survey up into manageable
        # chunks, each of which can be allocated its own survex file.
        # This can be facilitated by putting different sections into
        # different inkscape layers.  The code generates a list of
        # equates which may contain redundant information if A is near
        # B, and B is near C, /and/ A is near C.  However survex
        # doesn't complain if there is redundant information in the
        # equate directives.  This is convenient since it allows a
        # list the pairwise comparisons /with the separations/, which
        # facilitates debugging which stations have been equated.
        
        # Equates is a list of dicts of (station_pair, separation)

        equates = []

        for pair in combinations(stations, 2):
            dl, _, _ = self.distance(pair[0]['pos'], pair[1]['pos'])
            if dl * scale_fac < self.options.tol:
                equates.append({'pair': pair, 'sepn': dl})

        # The /set/ of stations required for export.

        exports = set([f"{station['traverse']}.{station['id']}" for el in equates for station in el['pair']])

        # Make a dictionary to keep track of stations which should be
        # exported from a given traverse.  The key is the traverse
        # name.  The value is a list of stations to export.  If there
        # are no stations to export then the list is empty (rather
        # than there not being a key), initialised in the next line.

        exportd = dict([(traverse['id'], []) for traverse in traverses])
    
        for traverse_dot_station in exports:
            traverse, station = traverse_dot_station.split('.')
            exportd[traverse].append(station)

        # the top level enclosing *begin and *end is layer name or file name

        top_level = self.options.layer or os.path.splitext(svx_file)[0]
        
        # If we made it this far we're ready to write the survex file

        with open(os.path.join(self.options.directory, svx_file), 'w') as f:

            f.write(f"; survex file autogenerated from {self.svg.name}\n")

            if img_file is not None:
                f.write(f"; embedded image file name {img_file}\n")

            f.write(f"; generated {strftime('%c')}\n\n")

            f.write(f"; SVG orientation: ({nx}, {ny}) is {self.sprintd(self.options.north)}\n")
            f.write(f"; SVG orientation: ({ex}, {ey}) is {self.sprintd(self.options.north + 90)}\n")
            f.write(f"; SVG scale: {scale_len} is {self.options.scale} m, scale factor {scale_fac}\n")
            f.write(f"; SVG contained {ntraverse} traverses and {nstation} stations\n")
            f.write(f"; tolerance for identifying equates {self.options.tol} m\n\n")
            
            f.write(f"*begin {top_level}\n")

            if equates:
                for el in equates:
                    stations = [f"{station['traverse']}.{station['id']}" for station in el['pair']]
                    f.write(f"*equate {stations[0]} {stations[1]}; separation {el['sepn']} m\n")

            f.write("*data normal from to tape compass clino\n")

            for traverse in traverses:
                f.write(f"*begin {traverse['id']}\n")
                if exportd[traverse['id']]:
                    f.write('*export ' + ' '.join(map(str, sorted(exportd[traverse['id']]))) + '\n')
                for leg in traverse['legs']:
                    f.write(f"%3s %3s %7.2f %s 0\n" % (leg['from'], leg['to'], leg['tape'], self.sprintd(leg['compass'])))
                f.write(f"*end {traverse['id']}\n")

            f.write(f"*end {top_level}\n")
            f.write("; end of file\n")

        sys.stderr.write(f'Succesfully generated {svx_file}\n')

if __name__ == "__main__":
    ExportSurvex().run()
