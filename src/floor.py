#! /usr/bin/env python

import mapnik
stylesheet = 'floor.xml'
image = '../image/floor.png'
m = mapnik.Map(2600, 1300)
mapnik.load_map(m, stylesheet)
m.zoom_all() 
mapnik.render_to_file(m, image)
print("rendered image to {}".format(image))

