#!/usr/bin/env python
"""
svx_output.py
Python script for exporting survex (.svx) file from Inkscape

Copyright (C) 2015 Patrick B Warren

Email: patrickbwarren@gmail.com

Paper mail: Dr Patrick B Warren, 11 Bryony Way, Birkenhead,
  Merseyside, CH42 4LY, UK.

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
import math
from time import strftime
from itertools import combinations

import inkex
import simplepath
import simplestyle

def sprintd(b):
    "Takes a bearing and returns it as string in 000 format"
    while b < 0:
        b += 360
    b = int(b + 0.5)
    while b >= 360:
        b -= 360
    return '%03i' % b

def measure(steps):
    "Measure the distance between first two steps"
    dx = steps[1][1][0]-steps[0][1][0]
    dy = steps[1][1][1]-steps[0][1][1]
    dl = math.sqrt(dx*dx + dy*dy)
    return dx, dy, dl

e = inkex.Effect()

e.OptionParser.add_option('--tab', action = 'store',
                          type = 'string', dest = 'tab', default = '',
                          help = 'Dummy argument')

e.OptionParser.add_option('--scale', action = 'store',
                          type = 'float', dest = 'scale', default = '100.0',
                          help = 'Length of scale bar (in m)')

e.OptionParser.add_option('--north', action = 'store',
                          type = 'float', dest = 'north', default = '0.0',
                          help = 'Bearing for orientation line (in degrees)')
        
e.OptionParser.add_option('--tol', action = 'store',
                          type = 'float', dest = 'tol', default = '0.2',
                          help = 'Tolerance to equate stations (in m)')

e.OptionParser.add_option('--layer', action = 'store',
                          type = 'string', dest = 'layer', default = '',
                          help = 'Restrict conversion to a named layer')

e.OptionParser.add_option('--name', action = 'store',
                          type = 'string', dest = 'name', default = '',
                          help = 'Outermost begin-end block name')

e.getoptions()

svgfile = sys.argv[-1]

e.parse(svgfile)

svg = e.document.getroot()

docname = svg.attrib['{%s}docname' % inkex.NSS[u'sodipodi']]

# el = svg.find('.//svg:image', namespaces=inkex.NSS)
el = svg.find('.//{%(svg)s}image' % {'svg':inkex.NSS[u'svg']})
absref = el.attrib['{%s}absref' % inkex.NSS[u'sodipodi']]
imgfile = os.path.split(absref)[1]

# Figure out a name for the top level block, if not set as an option.

if e.options.name == '':
    if e.options.layer == '':
        e.options.name = os.path.splitext(docname)[0]
    else:
        e.options.name = e.options.layer

# Collect the pertinant path data by parsing the XML SVG file

# list = svg.findall('.//svg:g/svg:path', namespaces=inkex.NSS)
lines = svg.findall('.//{%(svg)s}g/{%(svg)s}path' % {'svg':inkex.NSS[u'svg']})

# Paths is a list of tuples (id, d, stroke, layer)

paths = [] 
  
for line in lines:
    stroke = simplestyle.parseStyle(line.attrib['style'])['stroke']
    layer = line.getparent().attrib['{%s}label' % inkex.NSS[u'inkscape']]
    paths.append((line.attrib['id'], line.attrib['d'], stroke, layer))

# Figure out the orientation (green is 00ff00)

subpaths = filter(lambda path: path[2] == '#00ff00', paths)

if not subpaths:
    print 'No green (stroke:#00ff00) orientation vector found'
    sys.exit(1)

# Construct the unit vector (nx, ny) to point along N, and the unit
# (ex, ey) to point along E.  We correct for north later.

steps = simplepath.parsePath(subpaths[0][1])
dx, dy, dl = measure(steps)
nx, ny = dx/dl, dy/dl
ex, ey = -ny, nx

# Figure out the scale (blue is 0000ff)

subpaths = filter(lambda path: path[2] == '#0000ff', paths)

if not subpaths:
    print 'No blue (stroke:#0000ff) scale bar found'
    sys.exit(1)

# Calculate the scale factor
    
steps = simplepath.parsePath(subpaths[0][1])
dx, dy, scalelen = measure(steps)
scalefac = e.options.scale / scalelen

# Now build the survex traverses.  Also keep track of stations and
# absolute positions to identify equates and exports.

paths = filter(lambda path: path[2] == '#ff0000', paths)

if e.options.layer != '':
    paths = filter(lambda path: path[3] == e.options.layer, paths)

if not paths:
    if e.options.layer == '':
        print 'No red (stroke:#ff0000) paths found'
    else:
        print 'No red (stroke:#ff0000) paths found in the layer "%s"' % e.options.layer
    sys.exit(1)

# Stations is a list of tuples of (traverse_name, station_id, x, y)
# Traverses is a list of tuples of (traverse_name, legs)
# Legs is a list of tuples of (from_id, to_id, tape, compass)

stations = []
traverses = []

for path in paths:
    steps = simplepath.parsePath(path[1])
    for i, step in enumerate(steps):
        stations.append((path[0], i, step[1][0], step[1][1]))
    legs = []
    for i in range(1, len(steps)):
        dx, dy, dl = measure(steps[i-1:])
        tape = scalefac * dl
        compass = e.options.north + math.degrees(math.atan2(ex*dx+ey*dy, nx*dx+ny*dy))
        legs.append((i-1, i, tape, compass))
    traverses.append((path[0], legs))

ntraverse = len(traverses)
nstation = len(stations)

# Identify the equates.  This is an O(n^2) pairwise comparison and
# more efficient methods are available but n should not get too large:
# for a large project it almost always bound to be a good idea to
# break the survey up into manageable chunks, each of which can be
# allocated its own survex file.  This can be facilitated by putting
# different sections into different inkscape layers.

# Equates is a list of tuples of (station, station, distance)
# where station is a tuple (traverse_name, station_id)

equates = []

for pair in combinations(stations, 2):
    dx = pair[0][2] - pair[1][2]
    dy = pair[0][3] - pair[1][3]
    dl = scalefac * math.sqrt(dx*dx + dy*dy)
    if dl < e.options.tol:
        equates.append((pair[0][0:2], pair[1][0:2], dl))

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

# Exports is a set of stations where a station is a tuple
# (traverse_name, station_id)

exports = set()

for equate in equates:
    exports.add(equate[0])
    exports.add(equate[1])

# We use a dictionary to keep track of stations which should be
# exported from a given traverse.

exportd = dict()

for traverse_name, station_id in exports:
    if traverse_name in exportd:
        exportd[traverse_name].append(station_id)
    else:
        exportd[traverse_name] = [station_id]

# If we made it this far we're ready to write the survex file

print '; survex file autogenerated from', docname
print '; embedded image file name', imgfile
print '; generated', strftime('%c')
print
print '; SVG orientation: (%g, %g) is ' % (nx, ny), sprintd(e.options.north)
print '; SVG orientation: (%g, %g) is ' % (ex, ey), sprintd(e.options.north + 90)
print '; SVG scale: %g is %g m, scale factor = %g' % (scalelen, e.options.scale, scalefac)
print '; SVG contained %i traverses and %i stations' % (ntraverse, nstation)
print '; tolerance for identifying equates = %g m' % e.options.tol
print
print '*data cylpolar from to tape compass depthchange'

if e.options.name != '':
    print
    print '*begin', e.options.name

if equates:
    print
for equate in equates:
    print '*equate %s.%i' % equate[0], '%s.%i' % equate[1], '; separation %0.2f m' % equate[2]

for traverse in traverses:
    print
    print '*begin', traverse[0]
    if traverse[0] in exportd:
        print '*export', ' '.join(sorted(map(str, exportd[traverse[0]])))
    for leg in traverse[1]:
        print '%3i %3i %7.2f ' % leg[0:3], sprintd(leg[3]), ' 0'
    print '*end', traverse[0]
    
if e.options.name != '':
    print
    print '*end', e.options.name

print
print '; end of file'

# End of python script
