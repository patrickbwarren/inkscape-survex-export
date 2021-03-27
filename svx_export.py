#!/usr/bin/env python
"""
svx_output.py
Python script for exporting survex (.svx) file from Inkscape

Copyright (C) 2015, 2020, 2021 Patrick B Warren

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

class PathError(Exception):
    pass

class ExportSurvex(inkex.EffectExtension):

    poly_lines = []

    def round360(self, x):
        "Converts an angle to a bearing in [0, 360)"
        return (x+360) if x < 0 else (x-360) if x >= 360 else x

    def delta(self, p0, p1):
        "Return dl, dx, dy between two AbsolutePathElements"
        x0, y0, x1, y1 = *p0.args, *p1.args
        dx, dy = x1-x0, y1-y0
        dl = sqrt(dx*dx + dy*dy)
        return dl, dx, dy

    def extract_line(self, color):
        "extract exactly one measuring line that matches color"
        subset = list(filter(lambda el: el['stroke'] == str(color.to_rgb()), self.poly_lines))
        if len(subset) == 0:
            raise PathError('no line found (check settings in color tabs)')
        elif len(subset) > 1:
            raise PathError('more than one line found (check settings in color tabs)')
        line = subset[0]['path']
        if len(line) != 2:
            raise PathError('line should be exactly two points')
        for seg in line:
            if not isinstance(seg, (inkex.paths.Move, inkex.paths.Line)):
                raise PathError('line should be straight')
        if self.options.debug: # write out discovered path
            sys.stderr.write(f"EXTRACTED: {subset[0]['layer']}.{subset[0]['id']} ({subset[0]['stroke']}):")
            for seg in line:
                sys.stderr.write(f" {seg.letter} {seg.args}")
            sys.stderr.write('\n')
        return line

    def path_clean(self, path):
        "Convert any horz or vert elements and return absolute path"
        path = path.to_absolute()
        for i, seg in enumerate(path):
            if isinstance(seg, (inkex.paths.Horz, inkex.paths.Vert)):
                path[i] = seg.to_line(path[i-1])
        return path

    def add_arguments(self, pars):

        pars.add_argument('--tab', help="Dummy argument")
        pars.add_argument('--directory', default=os.path.expanduser('~'), help="Destination directory")
        pars.add_argument('--file', help="Destination .svx file (with or without extension)")
        pars.add_argument('--option', help="File name defaults")
        pars.add_argument('--restrict', type=inkex.Boolean, help="Restrict export to current layer")
        pars.add_argument('--overwrite', type=inkex.Boolean, help="Overwrite .svx file if it already exists")
        pars.add_argument('--scale', type=float, default=100.0, help="Length of scale bar (in m)")
        pars.add_argument('--north', type=float, default=0.0, help="Bearing for orientation line (in degrees)")
        pars.add_argument('--tol', type=float, default=0.2, help="Tolerance to equate stations (in m)")
        pars.add_argument('--path-color', type=inkex.Color, default=inkex.Color("red"), help="Path export color")
        pars.add_argument('--scale-color', type=inkex.Color, default=inkex.Color("green"), help="Path export color")
        pars.add_argument('--orient-color', type=inkex.Color, default=inkex.Color("blue"), help="Path export color")
        pars.add_argument('--debug', type=inkex.Boolean, help="dump information")
        
    def effect(self):

        if not os.path.isdir(self.options.directory):
            raise inkex.AbortExtension("The specified directory does not exist")

        # Determine the image file name if there is one
        
        el = self.svg.find('.//svg:image', namespaces=inkex.NSS)
        s = '{%s}absref' % inkex.NSS[u'sodipodi']
        img_file = os.path.split(el.attrib[s])[1] if el is not None and s in el.attrib else None

        # Get the name of the currently selected layer if there is one
        
        el = self.svg.get_current_layer()
        s = '{%s}label' % inkex.NSS[u'inkscape']
        current_layer = el.attrib[s] if el is not None and s in el.attrib else None

        # Figure out the name of the .svx file
        
        if self.options.option == 'specified':
            file_name = self.options.file
        elif self.options.option == 'document':
            file_name = self.svg.name
        elif self.options.option == 'image':
            file_name = img_file
        elif self.options.option == 'layer':
            if current_layer is None:
                raise inkex.AbortExtension("No layer selected for setting file name")
            file_name = current_layer

        if file_name is None:
            raise inkex.AbortExtension("Could not construct .svx file name (no image etc)")

        svx_file = os.path.splitext(file_name)[0] + '.svx'

        if os.path.exists(os.path.join(self.options.directory, svx_file)) and not self.options.overwrite:
            raise inkex.AbortExtension(f"Aborting: {svx_file} already exists, and overwrite box not checked")

        # Find all the polylines in the drawing as a list of dicts of
        # (path, id, stroke, layer); path_clean removes Horz and Vert to
        # make path a list of inkex AbsolutePathCommands (Line, Move).

        for path in self.svg.findall('.//svg:g/svg:path', namespaces=inkex.NSS):
            stroke = dict(inkex.Style.parse_str(path.attrib['style']))['stroke']
            layer = path.getparent().attrib['{%s}label' % inkex.NSS[u'inkscape']]
            self.poly_lines.append({'path': self.path_clean(path.path),
                               'id': path.attrib['id'], 'stroke': stroke, 'layer': layer})

        if self.options.debug: # write out all discovered path data
            for line in self.poly_lines:
                sys.stderr.write(f"{line['layer']}.{line['id']} ({line['stroke']})\n")
                for seg in line['path']:
                    sys.stderr.write(f" {seg.letter} {seg.args}\n")
                    
        # Find the scale bar line and calculate the scale factor

        try:
            scale_len, _, _ = self.delta(*self.extract_line(self.options.scale_color))
            scale_fac = self.options.scale / scale_len
        except PathError as err:
            raise inkex.AbortExtension(f'Scale bar: {err}')

        # Find the orientation line (S-N) and construct the unit
        # vector (nx, ny) to point along N, and the unit (ex, ey) to
        # point along E.  These are notional directions, and the real
        # orientations are used in the calculations below.

        try:
            dl, dx, dy = self.delta(*self.extract_line(self.options.orient_color))
            nx, ny = -dx/dl, -dy/dl
            ex, ey = -ny, nx
        except PathError as err:
            raise inkex.AbortExtension(f'Orientation vector: {err}')

        # Find the exportable (poly)lines, restricted to selected layer if desired
        
        color = str(self.options.path_color.to_rgb())
        self.poly_lines = list(filter(lambda el: el['stroke'] == color, self.poly_lines))

        if self.options.restrict:
            if current_layer is None:
                raise inkex.AbortExtension("No layer selected to filter on")
            self.poly_lines = list(filter(lambda el: el['layer'] == current_layer, self.poly_lines))
            
        if not self.poly_lines:
            sys.stderr.write("No exportable lines found\n")
            sys.stderr.write("(check settings in color tabs and/or layer selection)\n")
            raise inkex.AbortExtension

        # Check the (poly)lines comprise straight line segments

        for line in self.poly_lines:
            for seg in line['path']:
                if not isinstance(seg, (inkex.paths.Move, inkex.paths.Line)):
                    sys.stderr.write("The below can be fixed by selecting all paths, then selecting all nodes\n")
                    sys.stderr.write("in node edit mode, and applying 'Make selected segments lines'\n")
                    raise inkex.AbortExtension(f"{line['id']} contains curved segments\n")

        # Now build the survex traverses:

        # stations is a list of dicts of (traverse_id, station_id, pos),
        # traverses is a list of dicts of (traverse_id, legs),
        # legs is a list of dicts of (from_id, to_id, tape, compass).

        # Keep track of stations and absolute positions to identify
        # equates and exports:

        stations = []
        traverses = []

        for line in self.poly_lines:
            legs = []
            for i, pos in enumerate(line['path']):
                stations.append({'traverse': line['id'], 'id': str(i), 'pos': pos})
                if i:
                    dl, dx, dy = self.delta(pos, prev)
                    tape = scale_fac * dl
                    compass = self.options.north + degrees(atan2(ex*dx+ey*dy, nx*dx+ny*dy))
                    legs.append({'from': str(i-1), 'to': str(i), 'tape': tape, 'compass': compass})
                prev = pos
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
        # equate directives.  This is convenient since it allows one
        # to list the pairwise comparisons with the separations, which
        # facilitates debugging if stations have not been equated.
        
        # Equates is a list of dicts of (station_pair, separation)

        equates = []

        for pair in combinations(stations, 2):
            dl, _, _ = self.delta(pair[0]['pos'], pair[1]['pos'])
            if dl * scale_fac < self.options.tol:
                equates.append({'pair': pair, 'sepn': dl})

        # The /set/ of stations required for export.

        exports = set([f"{station['traverse']}.{station['id']}"
                       for el in equates for station in el['pair']])

        # Make a dictionary to keep track of stations which should be
        # exported from a given traverse.  The key is the traverse
        # name.  The value is a list of stations to export.  If there
        # are no stations to export then the list is empty (rather
        # than there not being a key), initialised in the next line.

        exportd = dict([(traverse['id'], []) for traverse in traverses])
    
        for element in exports:
            traverse, station = element.split('.')
            exportd[traverse].append(station)

        # The top level enclosing *begin and *end is taken from file name

        top_level = os.path.splitext(svx_file)[0]
        
        # If we made it this far we're ready to write the survex file

        with open(os.path.join(self.options.directory, svx_file), 'w') as f:

            f.write(f"; {svx_file} autogenerated from {self.svg.name}\n")
            if img_file is not None:
                f.write(f"; embedded image file name {img_file}\n")
            f.write(f"; generated {strftime('%c')}\n\n")

            f.write(f"; SVG orientation: vector ({nx:0.3f}, {ny:0.3f}) is {self.round360(self.options.north):0.1f} degrees\n")
            f.write(f"; SVG orientation: vector ({ex:0.3f}, {ey:0.3f}) is {self.round360(self.options.north+90):0.1f} degrees\n")
            f.write(f"; SVG scale: {scale_len:0.2f} units = {self.options.scale:0.1f} m, scale factor {scale_fac:0.4f}\n")
            f.write(f"; SVG contained {ntraverse} traverses and {nstation} stations\n")
            f.write(f"; SVG tolerance for identifying equates {self.options.tol:0.2f} m\n")

            f.write(f"\n*begin {top_level}\n")

            if equates:
                f.write('\n')
                for el in equates:
                    stations = [f"{station['traverse']}.{station['id']}" for station in el['pair']]
                    f.write(f"*equate {stations[0]} {stations[1]} ; separation {el['sepn']:0.3f} m\n")

            f.write("\n*data normal from to tape compass clino\n")

            for traverse in traverses:
                if len(traverses) > 1:
                    f.write(f"\n*begin {traverse['id']}\n")
                if exportd[traverse['id']]:
                    f.write("*export " + ' '.join(map(str, sorted(exportd[traverse['id']]))) + '\n')
                f.write('\n')
                for leg in traverse['legs']:
                    f.write(f"{leg['from']:3s} {leg['to']:3s} {leg['tape']:8.3f} {self.round360(leg['compass']):6.1f} 0\n")
                if len(traverses) > 1:
                    f.write(f"\n*end {traverse['id']}\n")

            f.write(f"\n*end {top_level}\n")
            f.write("\n; end of file\n")

        sys.stderr.write(f"Successfully generated {svx_file}\n")

if __name__ == "__main__":
    ExportSurvex().run()
