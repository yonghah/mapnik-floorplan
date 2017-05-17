#! /usr/bin/env python

import mapnik
# import cairo
import sys


stylesheet = sys.argv[1]
w = int(sys.argv[2])
h = int(sys.argv[3])
filename = stylesheet.split('/')[-1]
image = '../image/{}.png'.format(filename)
m = mapnik.Map(w, h)
mapnik.load_map(m, stylesheet)
m.zoom_all()
mapnik.render_to_file(m, image)
print("rendered image to {}".format(image))

# surface = cairo.PDFSurface('../image/floor.pdf', m.width, m.height)
# mapnik.render(m, surface)
# surface.finish()
