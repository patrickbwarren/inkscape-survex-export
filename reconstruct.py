#!/usr/bin/env python
#!/usr/bin/env python

"""
reconstruct.py
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

import inkex
import simplepath
import simplestyle

def sprintd(b):
    "Takes a bearing and returns it as string in 000 format"
    while (b < 0):
        b += 360
    b = int(b + 0.5)
    while (b >= 360):
        b -= 360
    return "%03i" % b

station_x = []
station_y = []
station_id = []

def push_station(x, y, station):
    station_x.append(x)
    station_y.append(y)
    station_id.append(station)

print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)

print 'Final argument: ', sys.argv[-1]

e = inkex.Effect()

e.OptionParser.add_option('--tab', action = 'store',
                          type = 'string', dest = 'tab', default = '',
                          help = 'Dummy argument')

e.OptionParser.add_option('--scale', action = 'store',
                          type = 'float', dest = 'scale', default = '100.0',
                          help = 'Length of scale bar (in m)')

e.OptionParser.add_option('--bearing', action = 'store',
                          type = 'float', dest = 'bearing', default = '0.0',
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

e.OptionParser.add_option('--extra', action = 'store',
                          type = 'string', dest = 'extra', default = 'false',
                          help = 'Include extra information in output')

e.getoptions()

print 'scale = ', e.options.scale
print 'bearing = ', e.options.bearing
print 'tol = ', e.options.tol

if e.options.layer == '':
    print 'unrestricted export'
else:
    print 'restricting export to layer = ', e.options.layer

if e.options.name != '':
    print 'begin-end block name = ', e.options.name
else:
    print 'using default begin-end block name' 

if e.options.extra == "true":
    print 'including extra information in file'
else:
    print 'not including extra information in file'

svgfile = sys.argv[-1]

e.parse(svgfile)

svg = e.document.getroot()

docname = svg.attrib['{%s}docname' % inkex.NSS[u'sodipodi']]
print 'docname =', docname

el = svg.find('.//svg:image', namespaces=inkex.NSS)
absref = el.attrib['{%s}absref' % inkex.NSS[u'sodipodi']]
path, img = os.path.split(absref)
print 'image path =', path
print 'image file = ', img

# Collect the pertinant path data by parsing the XML SVG file

path_id = []
path_d = []
path_stroke = []
path_layer = []
  
list = svg.findall('.//svg:g/svg:path', namespaces=inkex.NSS)

for path in list:
    path_id.append(path.attrib['id'])
    path_d.append(path.attrib['d'])
    path_stroke.append(simplestyle.parseStyle(path.attrib['style'])['stroke'])
    path_layer.append(path.getparent().attrib['{%s}label' % inkex.NSS[u'inkscape']])

# Figure out a name for the top level block, if not set as an option.

if e.options.name == '':
    if e.options.layer == '':
        e.options.name = os.path.splitext(docname)[0]
    else:
        e.options.name = e.options.layer

# Figure out the orientation vector (green is 00ff00)

found = False

for i in range(len(path_id)):
    if path_stroke[i] == '#00ff00':
        found = True
        break

if not found:
    print "No green (stroke:#00ff00) orientation vector found"
    sys.exit(1)

# Construct the unit vector (nx, ny) to point along N, and the unit
# (ex, ey) to point along E.  We correct for the bearing later.

steps = simplepath.parsePath(path_d[i])

dx = steps[1][1][0] - steps[0][1][0]
dy = steps[1][1][1] - steps[0][1][1]

dl = math.sqrt(dx*dx + dy*dy)

nx = dx / dl
ny = dy / dl

ex = - ny
ey = nx

# Figure out the scale vector (blue is 0000ff) and calculate scale factor

found = False

for i in range(len(path_id)):
    if path_stroke[i] == '#0000ff':
        found = True
        break

if not found:
    print "No blue (stroke:#0000ff) scale bar found"
    sys.exit(1)

steps = simplepath.parsePath(path_d[i])

dx = steps[1][1][0] - steps[0][1][0]
dy = steps[1][1][1] - steps[0][1][1]

dl = math.sqrt(dx*dx + dy*dy)

sf = e.options.scale / dl

print dx, dy
print dl
print sf

#print path_id[i]
#print path_d[i]
#print path_stroke[i]
#print path_layer[i]
