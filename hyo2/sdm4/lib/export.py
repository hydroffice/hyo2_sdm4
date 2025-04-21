import logging
import os

import numpy as np
from osgeo import ogr, gdal, osr

from hyo2.abc2.lib.gdal_aux import GdalAux

logger = logging.getLogger(__name__)


class ExportDb:
    """Class that exports sound speed db data"""

    def __init__(self, db):
        _ = GdalAux()
        self.db = db

    @classmethod
    def export_folder(cls, output_folder):
        folder = os.path.join(output_folder, "export")
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    @classmethod
    def _create_ogr_lyr_and_fields(cls, ds):
        # create the only data layer
        lyr = ds.CreateLayer('soundspeed', None, ogr.wkbPoint)
        if lyr is None:
            logger.error("Layer creation failed")
            return

        field = ogr.FieldDefn('id', ogr.OFTInteger)
        if lyr.CreateField(field) != 0:
            raise RuntimeError("Creating field failed.")

        field = ogr.FieldDefn('time', ogr.OFTString)
        if lyr.CreateField(field) != 0:
            raise RuntimeError("Creating field failed.")

        field = ogr.FieldDefn('tss', ogr.OFTReal)
        if lyr.CreateField(field) != 0:
            raise RuntimeError("Creating field failed.")

        field = ogr.FieldDefn('draft', ogr.OFTReal)
        if lyr.CreateField(field) != 0:
            raise RuntimeError("Creating field failed.")

        field = ogr.FieldDefn('avg_depth', ogr.OFTReal)
        if lyr.CreateField(field) != 0:
            raise RuntimeError("Creating field failed.")

        return lyr

    def export_surface_speed_points(self, output_folder, ogr_format=GdalAux.ogr_formats['ESRI Shapefile']):

        output = os.path.join(self.export_folder(output_folder=output_folder), self.db.base_name)

        # create the data source
        try:
            with GdalAux.create_ogr_data_source(ogr_format=ogr_format, output_path=output) as ds:
                lyr = self._create_ogr_lyr_and_fields(ds)

                rows = self.db.list_points()
                if rows is None:
                    raise RuntimeError("Unable to retrieve profiles. Empty database?")
                if len(rows) == 0:
                    raise RuntimeError("Unable to retrieve profiles. Empty database?")

                for row in rows:

                    ft = ogr.Feature(lyr.GetLayerDefn())
                    ft.SetField('id', int(row[0]))
                    ft.SetField('time', row[1].isoformat())
                    ft.SetField('tss', float(row[3]))
                    ft.SetField('draft', float(row[4]))
                    ft.SetField('avg_depth', float(row[5]))

                    pt = ogr.Geometry(ogr.wkbPoint)
                    pt.SetPointZM(0, float(row[2].x), float(row[2].y), float(row[4]), float(row[3]))

                    try:
                        ft.SetGeometry(pt)

                    except Exception as e:
                        RuntimeError("%s > pt: %s, %s" % (e, row[2].x, row[2].y))

                    if lyr.CreateFeature(ft) != 0:
                        raise RuntimeError("Unable to create feature")
                    ft.Destroy()

        except RuntimeError as e:
            logger.error("%s" % e)
            return

        return

    def rasterize_surface_speed_points(self, output_folder):

        # output files
        output_float = os.path.join(self.export_folder(output_folder=output_folder), self.db.base_name + "_float.tif")
        if os.path.exists(output_float):
            os.remove(output_float)
        output_color = os.path.join(self.export_folder(output_folder=output_folder), self.db.base_name + "_color.tif")
        if os.path.exists(output_color):
            os.remove(output_color)

        # first retrieve the point positions
        lats = list()
        longs = list()
        tsss = list()
        rows = self.db.list_points()
        for row in rows:
            lats.append(row[2].y)
            longs.append(row[2].x)
            tsss.append(row[3])

        # retrieve geospatial info
        min_lat, max_lat, avg_lat = min(lats), max(lats), sum(lats) / len(lats)
        range_lat = max_lat - min_lat
        min_long, max_long, avg_long = min(longs), max(longs), sum(longs) / len(longs)
        range_long = max_long - min_long
        min_tss, max_tss = min(tsss), max(tsss)
        range_tss = max_tss - min_tss
        logger.debug("lat: %s / %s / %s" % (min_lat, max_lat, range_lat))
        logger.debug("long: %s / %s / %s" % (min_long, max_long, range_long))
        logger.debug("tss: %s / %s / %s" % (min_tss, max_tss, range_tss))

        # geographic srs
        geo_srs = osr.SpatialReference()
        geo_srs.ImportFromEPSG(4326)
        geo_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        # UTM srs
        utm_zone = GdalAux.lat_long_to_zone_number(lat=avg_lat, long=avg_long)
        utm_srs = osr.SpatialReference()
        utm_north = False
        if avg_lat > 0:
            utm_north = True
        utm_srs.SetUTM(utm_zone, utm_north)
        utm_srs.SetWellKnownGeogCS('WGS84')

        # from GEO to UTM
        coord_transform = osr.CoordinateTransformation(geo_srs, utm_srs)

        # geographic at poles
        use_geographic = (max_lat > 80) or (min_lat < -80)

        if use_geographic:
            logger.debug("use geographic")
            buffer = 0.05 * max(range_lat, range_long)
            x_min = min_long - buffer
            x_max = max_long + buffer
            y_min = min_lat - buffer
            y_max = max_lat + buffer

        else:
            logger.debug("use UTM")

            min_point = ogr.Geometry(ogr.wkbPoint)
            min_point.AddPoint(min_long, min_lat)
            min_point.Transform(coord_transform)
            min_e = min_point.GetX()
            min_n = min_point.GetY()

            max_point = ogr.Geometry(ogr.wkbPoint)
            max_point.AddPoint(max_long, max_lat)
            max_point.Transform(coord_transform)
            max_e = max_point.GetX()
            max_n = max_point.GetY()

            buffer = 0.05 * max(max_n - min_n, max_e - min_e)
            x_min = min_e - buffer
            x_max = max_e + buffer
            y_min = min_n - buffer
            y_max = max_n + buffer

        if len(lats) < 40:
            x_pixels = 100
        elif len(lats) < 100:
            x_pixels = 200
        elif len(lats) < 1000:
            x_pixels = 400
        else:
            x_pixels = 1000
        pixel_size = (x_max - x_min) / x_pixels
        y_pixels = int((y_max - y_min) / pixel_size) + 1
        logger.debug("pixels -> x: %s, y: %s, size: %s, samples: %s" % (x_pixels, y_pixels, pixel_size, len(lats)))

        array = np.zeros((y_pixels, x_pixels), dtype=np.float32)
        for idx, lat in enumerate(lats):

            if use_geographic:
                idx_lat = y_pixels - 1 - int((lat - y_min + pixel_size / 2.0) / pixel_size)
                idx_long = int((longs[idx] - x_min - pixel_size / 2.0) / pixel_size)
            else:
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(longs[idx], lat)
                point.Transform(coord_transform)
                e = point.GetX()
                n = point.GetY()

                idx_lat = y_pixels - 1 - int((n - y_min + pixel_size / 2.0) / pixel_size)
                idx_long = int((e - x_min - pixel_size / 2.0) / pixel_size)
            array[idx_lat, idx_long] = tsss[idx]

        driver = gdal.GetDriverByName('GTiff')

        # float geotiff
        ds = driver.Create(output_float, x_pixels, y_pixels, 1, gdal.GDT_Float32)
        ds.SetGeoTransform([x_min, pixel_size, 0, y_max, 0, -pixel_size])

        if use_geographic:
            ds.SetProjection(geo_srs.ExportToWkt())
        else:
            ds.SetProjection(utm_srs.ExportToWkt())

        ds.GetRasterBand(1).SetNoDataValue(0.0)
        ds.GetRasterBand(1).WriteArray(array=array)

        ds.FlushCache()

        # color geotiff
        ds = driver.Create(output_color, x_pixels, y_pixels, 1, gdal.GDT_Byte)
        ds.SetGeoTransform([x_min, pixel_size, 0, y_max, 0, -pixel_size])
        ct = self.rainbow_colortable(driver)
        ds.GetRasterBand(1).SetRasterColorTable(ct)

        if use_geographic:
            ds.SetProjection(geo_srs.ExportToWkt())
        else:
            ds.SetProjection(utm_srs.ExportToWkt())

        ds.GetRasterBand(1).SetNoDataValue(0.0)
        array[array != 0.0] = 255 * ((array[array != 0.0] - min_tss) / range_tss)
        ds.GetRasterBand(1).WriteArray(array=array.astype(int))

        ds.FlushCache()

    @classmethod
    def rainbow_colortable(cls, _):

        ct = gdal.ColorTable()
        ct.SetColorEntry(0, (255, 255, 255, 0))
        ct.SetColorEntry(1, (152, 0, 86))
        ct.SetColorEntry(2, (158, 0, 82))
        ct.SetColorEntry(3, (164, 0, 77))
        ct.SetColorEntry(4, (169, 0, 72))
        ct.SetColorEntry(5, (175, 0, 67))
        ct.SetColorEntry(6, (181, 0, 62))
        ct.SetColorEntry(7, (186, 0, 58))
        ct.SetColorEntry(8, (192, 0, 53))
        ct.SetColorEntry(9, (197, 0, 48))
        ct.SetColorEntry(10, (203, 0, 43))
        ct.SetColorEntry(11, (209, 0, 38))
        ct.SetColorEntry(12, (214, 0, 33))
        ct.SetColorEntry(13, (220, 0, 28))
        ct.SetColorEntry(14, (225, 0, 24))
        ct.SetColorEntry(15, (231, 0, 19))
        ct.SetColorEntry(16, (237, 0, 14))
        ct.SetColorEntry(17, (242, 0, 9))
        ct.SetColorEntry(18, (248, 0, 4))
        ct.SetColorEntry(19, (254, 0, 0))
        ct.SetColorEntry(20, (254, 3, 0))
        ct.SetColorEntry(21, (254, 7, 0))
        ct.SetColorEntry(22, (254, 11, 0))
        ct.SetColorEntry(23, (254, 15, 0))
        ct.SetColorEntry(24, (254, 19, 0))
        ct.SetColorEntry(25, (254, 23, 0))
        ct.SetColorEntry(26, (254, 27, 0))
        ct.SetColorEntry(27, (254, 31, 0))
        ct.SetColorEntry(28, (254, 35, 0))
        ct.SetColorEntry(29, (254, 39, 0))
        ct.SetColorEntry(30, (254, 43, 0))
        ct.SetColorEntry(31, (254, 47, 0))
        ct.SetColorEntry(32, (254, 50, 0))
        ct.SetColorEntry(33, (254, 54, 0))
        ct.SetColorEntry(34, (254, 58, 0))
        ct.SetColorEntry(35, (254, 62, 0))
        ct.SetColorEntry(36, (254, 66, 0))
        ct.SetColorEntry(37, (254, 70, 0))
        ct.SetColorEntry(38, (254, 74, 0))
        ct.SetColorEntry(39, (254, 78, 0))
        ct.SetColorEntry(40, (254, 82, 0))
        ct.SetColorEntry(41, (254, 86, 0))
        ct.SetColorEntry(42, (254, 90, 0))
        ct.SetColorEntry(43, (254, 94, 0))
        ct.SetColorEntry(44, (254, 98, 0))
        ct.SetColorEntry(45, (254, 101, 0))
        ct.SetColorEntry(46, (254, 105, 0))
        ct.SetColorEntry(47, (254, 109, 0))
        ct.SetColorEntry(48, (254, 113, 0))
        ct.SetColorEntry(49, (254, 117, 0))
        ct.SetColorEntry(50, (254, 121, 0))
        ct.SetColorEntry(51, (254, 125, 0))
        ct.SetColorEntry(52, (254, 129, 0))
        ct.SetColorEntry(53, (254, 133, 0))
        ct.SetColorEntry(54, (254, 137, 0))
        ct.SetColorEntry(55, (254, 141, 0))
        ct.SetColorEntry(56, (254, 145, 0))
        ct.SetColorEntry(57, (254, 149, 0))
        ct.SetColorEntry(58, (254, 152, 0))
        ct.SetColorEntry(59, (254, 156, 0))
        ct.SetColorEntry(60, (254, 160, 0))
        ct.SetColorEntry(61, (254, 164, 0))
        ct.SetColorEntry(62, (254, 168, 0))
        ct.SetColorEntry(63, (254, 172, 0))
        ct.SetColorEntry(64, (254, 176, 0))
        ct.SetColorEntry(65, (254, 180, 0))
        ct.SetColorEntry(66, (254, 184, 0))
        ct.SetColorEntry(67, (254, 188, 0))
        ct.SetColorEntry(68, (254, 192, 0))
        ct.SetColorEntry(69, (254, 196, 0))
        ct.SetColorEntry(70, (254, 200, 0))
        ct.SetColorEntry(71, (254, 203, 0))
        ct.SetColorEntry(72, (254, 207, 0))
        ct.SetColorEntry(73, (254, 211, 0))
        ct.SetColorEntry(74, (254, 215, 0))
        ct.SetColorEntry(75, (254, 219, 0))
        ct.SetColorEntry(76, (254, 223, 0))
        ct.SetColorEntry(77, (254, 227, 0))
        ct.SetColorEntry(78, (254, 231, 0))
        ct.SetColorEntry(79, (254, 235, 0))
        ct.SetColorEntry(80, (254, 239, 0))
        ct.SetColorEntry(81, (254, 243, 0))
        ct.SetColorEntry(82, (254, 247, 0))
        ct.SetColorEntry(83, (254, 251, 0))
        ct.SetColorEntry(84, (255, 255, 0))
        ct.SetColorEntry(85, (250, 255, 0))
        ct.SetColorEntry(86, (245, 255, 0))
        ct.SetColorEntry(87, (240, 255, 0))
        ct.SetColorEntry(88, (235, 255, 0))
        ct.SetColorEntry(89, (230, 255, 0))
        ct.SetColorEntry(90, (225, 255, 0))
        ct.SetColorEntry(91, (220, 255, 0))
        ct.SetColorEntry(92, (215, 255, 0))
        ct.SetColorEntry(93, (210, 255, 0))
        ct.SetColorEntry(94, (205, 255, 0))
        ct.SetColorEntry(95, (201, 255, 0))
        ct.SetColorEntry(96, (196, 255, 0))
        ct.SetColorEntry(97, (191, 255, 0))
        ct.SetColorEntry(98, (186, 255, 0))
        ct.SetColorEntry(99, (181, 255, 0))
        ct.SetColorEntry(100, (176, 255, 0))
        ct.SetColorEntry(101, (171, 255, 0))
        ct.SetColorEntry(102, (166, 255, 0))
        ct.SetColorEntry(103, (161, 255, 0))
        ct.SetColorEntry(104, (156, 255, 0))
        ct.SetColorEntry(105, (152, 255, 0))
        ct.SetColorEntry(106, (147, 255, 0))
        ct.SetColorEntry(107, (142, 255, 0))
        ct.SetColorEntry(108, (137, 255, 0))
        ct.SetColorEntry(109, (132, 255, 0))
        ct.SetColorEntry(110, (127, 255, 0))
        ct.SetColorEntry(111, (122, 255, 0))
        ct.SetColorEntry(112, (117, 255, 0))
        ct.SetColorEntry(113, (112, 255, 0))
        ct.SetColorEntry(114, (107, 255, 0))
        ct.SetColorEntry(115, (102, 255, 0))
        ct.SetColorEntry(116, (98, 255, 0))
        ct.SetColorEntry(117, (93, 255, 0))
        ct.SetColorEntry(118, (88, 255, 0))
        ct.SetColorEntry(119, (83, 255, 0))
        ct.SetColorEntry(120, (78, 255, 0))
        ct.SetColorEntry(121, (73, 255, 0))
        ct.SetColorEntry(122, (68, 255, 0))
        ct.SetColorEntry(123, (63, 255, 0))
        ct.SetColorEntry(124, (58, 255, 0))
        ct.SetColorEntry(125, (53, 255, 0))
        ct.SetColorEntry(126, (49, 255, 0))
        ct.SetColorEntry(127, (44, 255, 0))
        ct.SetColorEntry(128, (39, 255, 0))
        ct.SetColorEntry(129, (34, 255, 0))
        ct.SetColorEntry(130, (29, 255, 0))
        ct.SetColorEntry(131, (24, 255, 0))
        ct.SetColorEntry(132, (19, 255, 0))
        ct.SetColorEntry(133, (14, 255, 0))
        ct.SetColorEntry(134, (9, 255, 0))
        ct.SetColorEntry(135, (4, 255, 0))
        ct.SetColorEntry(136, (0, 255, 0))
        ct.SetColorEntry(137, (0, 255, 7))
        ct.SetColorEntry(138, (0, 255, 14))
        ct.SetColorEntry(139, (0, 255, 21))
        ct.SetColorEntry(140, (0, 255, 28))
        ct.SetColorEntry(141, (0, 255, 35))
        ct.SetColorEntry(142, (0, 255, 42))
        ct.SetColorEntry(143, (0, 255, 49))
        ct.SetColorEntry(144, (0, 255, 56))
        ct.SetColorEntry(145, (0, 255, 63))
        ct.SetColorEntry(146, (0, 255, 70))
        ct.SetColorEntry(147, (0, 255, 77))
        ct.SetColorEntry(148, (0, 255, 84))
        ct.SetColorEntry(149, (0, 255, 92))
        ct.SetColorEntry(150, (0, 255, 99))
        ct.SetColorEntry(151, (0, 255, 106))
        ct.SetColorEntry(152, (0, 255, 113))
        ct.SetColorEntry(153, (0, 255, 120))
        ct.SetColorEntry(154, (0, 255, 127))
        ct.SetColorEntry(155, (0, 255, 134))
        ct.SetColorEntry(156, (0, 255, 141))
        ct.SetColorEntry(157, (0, 255, 148))
        ct.SetColorEntry(158, (0, 255, 155))
        ct.SetColorEntry(159, (0, 255, 162))
        ct.SetColorEntry(160, (0, 255, 169))
        ct.SetColorEntry(161, (0, 255, 177))
        ct.SetColorEntry(162, (0, 255, 184))
        ct.SetColorEntry(163, (0, 255, 191))
        ct.SetColorEntry(164, (0, 255, 198))
        ct.SetColorEntry(165, (0, 255, 205))
        ct.SetColorEntry(166, (0, 255, 212))
        ct.SetColorEntry(167, (0, 255, 219))
        ct.SetColorEntry(168, (0, 255, 226))
        ct.SetColorEntry(169, (0, 255, 233))
        ct.SetColorEntry(170, (0, 255, 240))
        ct.SetColorEntry(171, (0, 255, 247))
        ct.SetColorEntry(172, (0, 255, 255))
        ct.SetColorEntry(173, (0, 249, 255))
        ct.SetColorEntry(174, (0, 244, 255))
        ct.SetColorEntry(175, (0, 239, 255))
        ct.SetColorEntry(176, (0, 234, 255))
        ct.SetColorEntry(177, (0, 229, 255))
        ct.SetColorEntry(178, (0, 224, 255))
        ct.SetColorEntry(179, (0, 219, 255))
        ct.SetColorEntry(180, (0, 214, 255))
        ct.SetColorEntry(181, (0, 209, 255))
        ct.SetColorEntry(182, (0, 203, 255))
        ct.SetColorEntry(183, (0, 198, 255))
        ct.SetColorEntry(184, (0, 193, 255))
        ct.SetColorEntry(185, (0, 188, 255))
        ct.SetColorEntry(186, (0, 183, 255))
        ct.SetColorEntry(187, (0, 178, 255))
        ct.SetColorEntry(188, (0, 173, 255))
        ct.SetColorEntry(189, (0, 168, 255))
        ct.SetColorEntry(190, (0, 163, 255))
        ct.SetColorEntry(191, (0, 158, 255))
        ct.SetColorEntry(192, (0, 152, 255))
        ct.SetColorEntry(193, (0, 147, 255))
        ct.SetColorEntry(194, (0, 142, 255))
        ct.SetColorEntry(195, (0, 137, 255))
        ct.SetColorEntry(196, (0, 132, 255))
        ct.SetColorEntry(197, (0, 127, 255))
        ct.SetColorEntry(198, (0, 122, 255))
        ct.SetColorEntry(199, (0, 117, 255))
        ct.SetColorEntry(200, (0, 112, 255))
        ct.SetColorEntry(201, (0, 107, 255))
        ct.SetColorEntry(202, (0, 101, 255))
        ct.SetColorEntry(203, (0, 96, 255))
        ct.SetColorEntry(204, (0, 91, 255))
        ct.SetColorEntry(205, (0, 86, 255))
        ct.SetColorEntry(206, (0, 81, 255))
        ct.SetColorEntry(207, (0, 76, 255))
        ct.SetColorEntry(208, (0, 71, 255))
        ct.SetColorEntry(209, (0, 66, 255))
        ct.SetColorEntry(210, (0, 61, 255))
        ct.SetColorEntry(211, (0, 56, 255))
        ct.SetColorEntry(212, (0, 51, 255))
        ct.SetColorEntry(213, (0, 45, 255))
        ct.SetColorEntry(214, (0, 40, 255))
        ct.SetColorEntry(215, (0, 35, 255))
        ct.SetColorEntry(216, (0, 30, 255))
        ct.SetColorEntry(217, (0, 25, 255))
        ct.SetColorEntry(218, (0, 20, 255))
        ct.SetColorEntry(219, (0, 15, 255))
        ct.SetColorEntry(220, (0, 10, 255))
        ct.SetColorEntry(221, (0, 5, 255))
        ct.SetColorEntry(222, (0, 0, 255))
        ct.SetColorEntry(223, (3, 0, 250))
        ct.SetColorEntry(224, (7, 0, 246))
        ct.SetColorEntry(225, (10, 0, 242))
        ct.SetColorEntry(226, (14, 0, 238))
        ct.SetColorEntry(227, (17, 0, 234))
        ct.SetColorEntry(228, (21, 0, 230))
        ct.SetColorEntry(229, (24, 0, 226))
        ct.SetColorEntry(230, (28, 0, 222))
        ct.SetColorEntry(231, (31, 0, 218))
        ct.SetColorEntry(232, (35, 0, 214))
        ct.SetColorEntry(233, (38, 0, 210))
        ct.SetColorEntry(234, (42, 0, 206))
        ct.SetColorEntry(235, (45, 0, 202))
        ct.SetColorEntry(236, (49, 0, 198))
        ct.SetColorEntry(237, (52, 0, 194))
        ct.SetColorEntry(238, (56, 0, 190))
        ct.SetColorEntry(239, (59, 0, 186))
        ct.SetColorEntry(240, (63, 0, 182))
        ct.SetColorEntry(241, (67, 0, 178))
        ct.SetColorEntry(242, (70, 0, 174))
        ct.SetColorEntry(243, (74, 0, 170))
        ct.SetColorEntry(244, (77, 0, 166))
        ct.SetColorEntry(245, (81, 0, 162))
        ct.SetColorEntry(246, (84, 0, 158))
        ct.SetColorEntry(247, (88, 0, 154))
        ct.SetColorEntry(248, (91, 0, 150))
        ct.SetColorEntry(249, (95, 0, 146))
        ct.SetColorEntry(250, (98, 0, 142))
        ct.SetColorEntry(251, (102, 0, 138))
        ct.SetColorEntry(252, (105, 0, 134))
        ct.SetColorEntry(253, (109, 0, 130))
        ct.SetColorEntry(254, (112, 0, 126))
        ct.SetColorEntry(255, (116, 0, 122))

        return ct
