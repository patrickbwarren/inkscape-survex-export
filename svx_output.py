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

import os, sys, math
from time import strftime
from itertools import combinations
import inkex, simplepath, simplestyle

# Define a (trivial) exception class to catch path errors

class PathError(Exception):
    pass

def sprintd(b):
    "Takes a bearing and returns it as string in 000 format"
    while b < 0: b += 360
    b = int(b + 0.5)
    while b >= 360: b -= 360
    return '%03i' % b

def distance(p1, p2):
    "Calculate the distance between two points"
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dl = math.sqrt(dx*dx + dy*dy)
    return dx, dy, dl

def measure(steps):
    "Measure the distance between first two steps"
    return distance(steps[0][1], steps[1][1])

msg = None

e = inkex.Effect()

e.arg_parser.add_argument('--tab', help='Dummy argument')
e.arg_parser.add_argument('--scale', type=float, default=100.0, help='Length of scale bar (in m)')
e.arg_parser.add_argument('--north', type=float, default=0.0, help='Bearing for orientation line (in degrees)')
e.arg_parser.add_argument('--tol', type=float, default=0.2, help='Tolerance to equate stations (in m)')
e.arg_parser.add_argument('--layer', default=None, help='Restrict conversion to a named layer')
e.arg_parser.add_argument('--cpaths', default='#ff0000', help='Color of (poly)lines for export (default #ff0000)')
e.arg_parser.add_argument('--cnorth', default='#00ff00', help='Color of orientation line (default #00ff00)')
e.arg_parser.add_argument('--cscale', default='#0000ff', help='Color of scale bar line (default #0000ff)')

args = e.arg_parser.parse_args()

# Parse the SVG file which is passed as the last command line argument

# The commented out 'svg.find' and 'svg.findall' statements below show
# the correct way to to pass namespaces, however it appears they do
# not work on Windows.  Therefore the actual statements used are
# kludges which use a named argument in a string format.

print(sys.argv[-1])

e.svg.parse(sys.argv[-1])

# Find out some basic properties

svg = e.document.getroot()

s = '{%s}docname' % inkex.NSS[u'sodipodi']

if s in svg.attrib:
    docname = svg.attrib[s]
else:
    docname = 'untitled'

if args.layer is None:
    toplevel = os.path.splitext(docname)[0]
else:
    toplevel = args.layer

# el = svg.find('.//svg:image', namespaces=inkex.NSS)
el = svg.find('.//{%(svg)s}image' % {'svg':inkex.NSS[u'svg']})

s = '{%s}absref' % inkex.NSS[u'sodipodi']
    
if el is not None and s in el.attrib:
    imgfile = os.path.split(el.attrib[s])[1]
else:
    imgfile = None

# Find all the (poly)lines in the document

# list = svg.findall('.//svg:g/svg:path', namespaces=inkex.NSS)
lines = svg.findall('.//{%(svg)s}g/{%(svg)s}path' % {'svg':inkex.NSS[u'svg']})

# Paths is a list of tuples (id, d, stroke, layer)

paths = [] 
  
for line in lines:
    stroke = simplestyle.parseStyle(line.attrib['style'])['stroke']
    layer = line.getparent().attrib['{%s}label' % inkex.NSS[u'inkscape']]
    paths.append((line.attrib['id'], line.attrib['d'], stroke, layer))

# We extract the information from the paths and raise a PathError
# exception if there is a problem.  This is caught (at the end) and
# the message (in msg) printed to stderr.

try:

    if not paths:
        msg = 'No paths found at all!'
        raise PathError

    # Find the orientation line.

    subpaths = filter(lambda path: path[2] == args.cnorth, paths)

    if not subpaths:
        msg = 'No orientation line found of color %s' % args.cnorth
        raise PathError

    # Construct the unit vector (nx, ny) to point along N, and the
    # unit (ex, ey) to point along E.  We correct for north later.

    steps = simplepath.parsePath(subpaths[0][1])
    dx, dy, dl = measure(steps)
    nx, ny = dx/dl, dy/dl
    ex, ey = -ny, nx

    # Find the scale bar line

    subpaths = filter(lambda path: path[2] == args.cscale, paths)

    if not subpaths:
        msg = 'No scale bar line found of color %s' % args.cscale
        raise PathError

    # Calculate the scale factor

    steps = simplepath.parsePath(subpaths[0][1])
    scale_len = measure(steps)[2]
    scale_fac = args.scale / scale_len

    # Find the exportable (poly)lines

    paths = filter(lambda path: path[2] == args.cpaths, paths)

    if not paths:
        msg = 'No exportable lines found of color %s' % args.cpaths
        raise PathError

    if args.layer is not None:
        paths = filter(lambda path: path[3] == args.layer, paths)
        if not paths:
            msg = 'No exportable lines found of color %s in layer %s' % (args.cpaths, args.layer)
            raise PathError

    # Now build the survex traverses.  Keep track of stations and
    # absolute positions to identify equates and exports.

    # Stations is a list of tuples of (x, y, traverse_name, station_id)
    # Traverses is a list of tuples of (traverse_name, legs), where
    # Legs is a list of tuples of (from_id, to_id, tape, compass)

    stations = []
    traverses = []

    for path in paths:
        legs = []
        steps = simplepath.parsePath(path[1])
        for i, step in enumerate(steps):
            stations.append((step[1][0], step[1][1], path[0], i))
            if i == 0: continue
            dx, dy, dl = distance(steps[i-1][1], step[1])
            tape = scale_fac * dl
            compass = args.north + math.degrees(math.atan2(ex*dx+ey*dy, nx*dx+ny*dy))
            legs.append((i-1, i, tape, compass))
        traverses.append((path[0], legs))

    ntraverse = len(traverses)
    nstation = len(stations)

    # Identify the equates.  This is an O(n^2) pairwise comparison and
    # more efficient methods are available but n should not get too
    # large: for a large project it almost always bound to be a good
    # idea to break the survey up into manageable chunks, each of
    # which can be allocated its own survex file.  This can be
    # facilitated by putting different sections into different
    # inkscape layers.

    # Equates is a list of tuples of (station, station, distance)
    # where station is a tuple (traverse_name, station_id)

    equates = []

    for pair in combinations(stations, 2):
        dl = scale_fac * distance(pair[0], pair[1])[2]
        if dl < args.tol:
            equates.append((pair[0][2:], pair[1][2:], dl))

    # Afficianados will notice this is a job only half done.  What we have
    # generated is an (incomplete) list of equivalence relations between
    # stations.  It may be incomplete because if A is near B, and B is
    # near C, it doesn't always follow that A is near enough C to satisfy
    # the closeness criterion.  What we should really do next is build the
    # set of equivalence classes of stations, then we can generate
    # precisely n-1 *equate directives for each non trivial equivalence
    # class of size n > 1.  In fact, survex allows for mutiple stations to
    # be listed in one *equate line, so we could just generate one *equate
    # directive for each non trivial equivalence class.  However survex
    # doesn't complain if there is redundant information in the equate
    # directives so below we take the easy option of using the list of
    # equivalence relations to generate a 1:1 list of equate directives.
    # Fastidiuous people may wish to tidy this up by hand afterwards.

    # Extract the set of stations required for export from the list of
    # equates.

    # Exports is a *set* of stations where a station is a tuple
    # (traverse_name, station_id)

    exports = set()

    for equate in equates:
        exports.add(equate[0])
        exports.add(equate[1])

    # Exportd is a dictionary to keep track of stations which should
    # be exported from a given traverse.  The key is the traverse
    # name.  The value is a list of stations to export.  If there are
    # no stations to export then the list is empty (rather than there
    # not being a key).

    exportd = dict()
    for traverse in traverses: exportd[traverse[0]] = []
    
    for traverse_name, station_id in exports:
            exportd[traverse_name].append(station_id)

    # If we made it this far we're ready to write the survex file

    gen_time = strftime('%c')

    print(f'; survex file autogenerated from {docname}')

    if imgfile is not None:
        print(f'; embedded image file name {imgfile}')

    print(f'; generated {gentime}\n')

    print(f'; SVG orientation: ({nx}, {ny}) is {sprintd(args.north)}')
    print(f'; SVG orientation: ({ex}, {ey}) is {sprintd(args.north + 90)}')
    print(f'; SVG scale: {scale_len} is {args.scale} m, scale factor {scale_fac}')
    print(f'; SVG contained {ntraverse} traverses and {nstation} stations')
    print(f'; tolerance for identifying equates {args.tol} m\n')

    print(f'*begin {toplevel}')

    if equates:
        for equate in equates:
            print('*equate %s.%i' % equate[0], '%s.%i' % equate[1], f'; separation {equate[2]} m')

    print('*data normal from to tape compass clino')

    for traverse in traverses:
        print(f'*begin {traverse[0]}')
        if exportd[traverse[0]]:
            print('*export ' + ' '.join(map(str, sorted(exportd[traverse[0]]))))
        for leg in traverse[1]:
            print(f'%3i %3i %7.2f {sprintd(leg[3])} 0' % leg[0:3], )
        print(f'*end {traverse[0]}')

    print(f'*end {toplevel}')
    print('; end of file')

except: PathError

if msg is not None:
    sys.stderr.write('Encountered a PathError:\n')
    sys.stderr.write(msg + '\n')
    sys.stderr.write('No survex file was generated')
    sys.exit(1)
else:
    sys.exit(0)

# End of python script
