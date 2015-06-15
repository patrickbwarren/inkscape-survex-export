#!/usr/bin/env python

import os
import sys

import inkex
import simplepath
import simplestyle

#print 'Number of arguments:', len(sys.argv), 'arguments.'
#print 'Argument List:', str(sys.argv)

#print 'Final argument: ', sys.argv[-1]

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

e.OptionParser.add_option('--restrict', action = 'store',
                          type = 'string', dest = 'restrict', default = 'false',
                          help = 'Restrict conversion to a named layer')

e.OptionParser.add_option('--layer', action = 'store',
                          type = 'string', dest = 'layer', default = '',
                          help = 'Name of layer')

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

if e.options.restrict == "true":
    print 'restricting export to layer = ', e.options.layer
else:
    print 'unrestricted export'

if e.options.name != '':
    print 'begin-end block name = ', e.options.name
else:
    print 'using default begin-end block name' 

if e.options.extra == "true":
    print 'including extra information in file'
else:
    print 'not including extra information in file'
    
e.parse(sys.argv[-1])

svg = e.document.getroot()

#import pprint
#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(svg.attrib)
#sys.exit(0)

docname = svg.attrib['{%s}docname' % inkex.NSS[u'sodipodi']]
print 'docname =', docname

el = svg.find('.//svg:image', namespaces=inkex.NSS)
absref = el.attrib['{%s}absref' % inkex.NSS[u'sodipodi']]
path, img = os.path.split(absref)
print 'image path =', path
print 'image file = ', img

print "\n\nSearch for paths\n"
                
list = svg.findall('.//svg:g/svg:path', namespaces=inkex.NSS)

for path in list:

    print "\npath id = ", path.attrib['id']
    print "d = ", path.attrib['d']
    print "style = ", path.attrib['style']
    print "layer = ", path.getparent().attrib['{%s}label' % inkex.NSS[u'inkscape']]

    stroke = simplestyle.parseStyle(path.attrib['style'])['stroke']
    print "stroke = ", stroke

    steps = simplepath.parsePath(path.attrib['d'])
    print "steps = ", steps
