#!/usr/bin/env python

import inkex
import os

import simplepath
import simplestyle

class ExportSurvexEffect(inkex.Effect):
    """
    Create a survex file from paths in the drawing.
    """
    def __init__(self):
        """
        Constructor.
        Defines the "--where" option of a script.
        """
        # Call the base class constructor.
        inkex.Effect.__init__(self)

        # Define string option "--where" with "-w" shortcut and default value "Default".
        self.OptionParser.add_option('-w', '--where', action = 'store',
          type = 'string', dest = 'where', default = 'Default',
          help = 'Where to save the survex file.')

    def effect(self):
        """
        Effect behaviour.
        """
        # Get script's "--where" option value.
        where = self.options.where

        # Get access to main SVG document element and find the first image.
        svg = self.document.getroot()

        el = svg.find('.//svg:image', namespaces=inkex.NSS)

        absref = el.attrib['{%s}absref' % inkex.NSS[u'sodipodi']]
        imgnoext, imgext = os.path.splitext(absref)
        head, tail = os.path.split(imgnoext)
        
        f1 = open(os.path.join(head, 'svg.log'), 'w')
        
        print >>f1, 'absref =', absref
        print >>f1, 'imgnoext, imgext =', imgnoext, imgext
        print >>f1, 'head, tail =', head, tail

        print >>f1, "\n\nSearch for paths\n"
                
        list = svg.findall('.//svg:g/svg:path', namespaces=inkex.NSS)

        for path in list:

            print >>f1, "\npath id = ", path.attrib['id']
            print >>f1, "d = ", path.attrib['d']
            print >>f1, "style = ", path.attrib['style']
            print >>f1, "layer = ", path.getparent().attrib['{%s}label' % inkex.NSS[u'inkscape']]

            stroke = simplestyle.parseStyle(path.attrib['style'])['stroke']
            print >>f1, "stroke = ", stroke

            steps = simplepath.parsePath(path.attrib['d'])
            print >>f1, "steps = ", steps
           
#            for k, v in path.attrib.iteritems():
#                print >>f1, "path:" , k, "-->", v

        f1.close()

# Create effect instance and apply it.

effect = ExportSurvexEffect()
effect.affect()
