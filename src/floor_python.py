#! /usr/bin/python

import mapnik
import psycopg2
import json


def main():

    bd = '1005037'
    flr = '03'
    angle = -0.03
    print_floor(bd, flr, angle)


def print_floor(bd, flr, angle):
    m = Map()
    st_floor = Sfs('Floor', '#000000')
    st_room = Sfs('Room', '#FFFFFF')
    st_graphic = Sls('Graphic', '#000000', 0.5)

    # name, table, field
    st_room_dept = Ufs('Dept', "dept.json", 'deptid')

    m.add_style(st_floor)
    m.add_style(st_room)
    m.add_style(st_room_dept)
    m.add_style(st_graphic)

    floor = Layer('floor', Datasource(bd, flr, 'floor', angle=angle).get())
    floor.add_style(st_floor)
    m.add_layer(floor)

    room = Layer('room', Datasource(
        bd, flr, 'room',
        angle=angle,
        fields=['deptid']).get())
    room.add_style(st_room_dept)
    m.add_layer(room)

    graphic = Layer('graphic',
                    Datasource(bd, flr, 'reference', angle=angle).get())
    graphic.add_style(st_graphic)
    m.add_layer(graphic)

    m.zoom_all()
    mapnik.render_to_file(m, '../image/world.png', 'png')
    print("rendered image to 'world.png'")


class Map(mapnik.Map):
    def __init__(self):
        width = 600
        height = 300
        mapnik.Map.__init__(self, width, height)
        self.background = mapnik.Color("white")
        self.srs = "+init=epsg:2253"

    def add_style(self, style):
        self.append_style(style.name, style)

    def add_layer(self, layer):
        self.layers.append(layer)


class Layer(mapnik.Layer):
    def __init__(self, name, datasource):
        mapnik.Layer.__init__(self, name)
        self.datasource = datasource

    def add_style(self, style):
        self.styles.append(style.name)


class Sfs(mapnik.Style):
    ''' simple fill style'''
    def __init__(self, name, color):
        mapnik.Style.__init__(self)
        self.name = name
        rule = mapnik.Rule()
        fsb = mapnik.PolygonSymbolizer()
        fsb.fill = mapnik.Color(color)
        rule.symbols.append(fsb)
        lsb = mapnik.LineSymbolizer()
        lsb.stroke = mapnik.Color("#FFFFFF")
        lsb.stroke_width = 0.0
        rule.symbols.append(lsb)
        self.rules.append(rule)


class Sls(mapnik.Style):
    ''' simple line style'''
    def __init__(self, name, color, width):
        mapnik.Style.__init__(self)
        self.name = name
        rule = mapnik.Rule()
        lsb = mapnik.LineSymbolizer()
        lsb.stroke = mapnik.Color(color)
        lsb.stroke_width = width
        rule.symbols.append(lsb)
        self.rules.append(rule)


class Ufs(mapnik.Style):
    '''Unique fill sytle. Under construction'''
    def __init__(self, name, config_file, field):
        mapnik.Style.__init__(self)
        self.name = name
        self.config = self.get_config(config_file)
        self.field = field
        print(self.config)
        self.create_rules(self.config["map"])

    def get_config(self, config_file):
        with open(config_file) as df:
            config = json.load(df)
        return config

    def create_rules(self, matches):
        for match in matches:
            rule = mapnik.Rule()
            rule.filter = mapnik.Filter(
                "[{}] = '{}'".format(self.field, match["key"]))
            rule.symbols.append(self.get_fill(match["value"]))
            rule.symbols.append(self.get_line("#FFFFFF", 0.0))
            self.rules.append(rule)

    def get_fill(self, color):
        fsb = mapnik.PolygonSymbolizer()
        c_code = color.encode('ascii', 'ignore')
        fsb.fill = mapnik.Color(c_code)
        return fsb

    def get_line(self, color, width):
        lsb = mapnik.LineSymbolizer()
        lsb.stroke = mapnik.Color(color)
        lsb.stroke_width = width
        return lsb


class Datasource:
    def __init__(self, bld, flr, table, angle=0, fields=[]):
        geometry = 'wkb_geometry'
        if angle != 0:
            ox, oy = get_origin(bld, flr)
            geometry = "ST_Rotate(wkb_geometry, {}, {}, {}) as \
                wkb_geometry".format(angle, ox, oy)
        more_fields = ''
        if fields:
            more_fields = ', ' + ', '.join(fields)
        self.query = "(select {} {} \
            from {} \
            where bldrecnbr='{}' \
            and floor='{}') as foo".format(
                geometry, more_fields, table, bld, flr)

    def get(self):
        return mapnik.PostGIS(
            host='localhost',
            dbname='geo',
            user='yonghah',
            password='1111',
            table=self.query,
            extent_from_subquery=True
        )


def get_origin(bd, flr):
    connection = psycopg2.connect(
        host='localhost',
        database="geo",
        user="yonghah",
        password="1111")
    cursor = connection.cursor()
    query = "SELECT ST_X(ST_Centroid(wkb_geometry)), \
        ST_Y(ST_Centroid(wkb_geometry)) from floor where bldrecnbr='{}' \
        and floor='{}'".format(bd, flr)
    cursor.execute(query)
    result = cursor.fetchone()
    return result


def get_bbox(rid):
    connection = psycopg2.connect(
        host='localhost',
        database="geo",
        user="yonghah",
        password="1111")
    cursor = connection.cursor()
    query = "SELECT ST_AsText(ST_Extent(wkb_geometry)) from room \
        where rmrecnbr='{}'".format(rid)
    cursor.execute(query)
    result = cursor.fetchone()
    return result


if __name__ == '__main__':
    main()
