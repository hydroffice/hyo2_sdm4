import datetime
import logging
import math
import os
import statistics
import traceback
from threading import Timer, Lock
from typing import Optional

from hyo2.abc2.lib.gdal_aux import GdalAux
from hyo2.abc2.lib.package.pkg_helper import PkgHelper
from hyo2.sdm4.lib.db import MonitorDb
from hyo2.sdm4.lib.estimate.abstractestimator import EstimatorType, EstimationModes
from hyo2.sdm4.lib.estimate.casttime.casttime import CastTime
from hyo2.sdm4.lib.readers.emseries import EmSeries
from hyo2.ssm2.lib.soundspeed import SoundSpeedLibrary

logger = logging.getLogger(__name__)


class SurveyDataMonitor:

    def __init__(self, ssm: SoundSpeedLibrary, timing: Optional[float] = 3.0) -> None:
        logger.debug("Init survey data monitor")
        self._ssm = ssm
        self._timing = timing

        self._active = False
        self._pause = False

        self._counter = 0
        self._last_dgtime = None

        self._default_draft = 5
        self._avg_depth = 1000
        self._has_sis_data = False
        self._cur_tss = None
        self._cur_draft = None
        self._cur_depth = None
        self._cur_time = None
        self._past_cast_time = None
        self._next_cast_time = None

        self._times = list()
        self._lats = list()
        self._longs = list()
        self._tsss = list()
        self._drafts = list()
        self._depths = list()
        self._data_info = str()

        self._lock = Lock()
        self._external_lock = False
        self.base_name = None

        self._cast_time = CastTime()
        self._cast_time.plotting_mode = False
        self._cast_time_updated = False

        self._active_estimator = EstimatorType.CAST_TIME

    @property
    def current_time(self) -> datetime.datetime:
        return self._cur_time

    @property
    def mode(self) -> EstimationModes:
        if self._active_estimator == EstimatorType.CAST_TIME:
            return self._cast_time.mode

        else:
            return EstimationModes.UNKNOWN

    @property
    def output_folder(self) -> str:
        out_folder = os.path.join(self._ssm.data_folder, "monitor")
        if not os.path.exists(out_folder):
            os.makedirs(out_folder)
        return out_folder

    def open_output_folder(self) -> None:
        PkgHelper.explore_folder(self.output_folder)

    def lock_data(self) -> None:
        self._lock.acquire()
        self._external_lock = True

    def unlock_data(self) -> None:
        self._lock.release()
        self._external_lock = False

    @property
    def default_draft(self) -> float:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._default_draft

    @default_draft.setter
    def default_draft(self, value: float) -> None:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        self._default_draft = value

    @property
    def avg_depth(self) -> float:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._avg_depth

    @avg_depth.setter
    def avg_depth(self, value: float) -> None:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        self._avg_depth = value

    @property
    def next_cast_time(self) -> datetime.datetime:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._next_cast_time

    @property
    def times(self) -> list:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._times

    @property
    def lats(self) -> list:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._lats

    @property
    def longs(self) -> list:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._longs

    @property
    def tsss(self) -> list:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._tsss

    @property
    def drafts(self) -> list:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._drafts

    @property
    def depths(self) -> list:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._depths

    @property
    def data_info(self) -> str:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")

        return self._data_info

    @property
    def next_cast_info(self) -> str:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")

        info = str()

        if self._active_estimator == EstimatorType.CAST_TIME:
            info += self._cast_time.info_message

        else:
            info += "N/A"

        # logger.debug("latest info: %s" % info)
        return info

    @property
    def active(self) -> bool:
        return self._active

    @property
    def active_estimator(self) -> EstimatorType:
        return self._active_estimator

    @property
    def casttime(self) -> CastTime:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._cast_time

    @property
    def casttime_updated(self) -> bool:
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._cast_time_updated

    def disable_estimation(self) -> None:
        logger.debug("disabled estimation")
        self._active_estimator = EstimatorType.DISABLED

    def activate_casttime(self) -> None:
        logger.debug("activate CastTime")
        self._active_estimator = EstimatorType.CAST_TIME

    def activate_forecast(self) -> None:
        logger.debug("activate ForeCast")
        self._active_estimator = EstimatorType.FORE_CAST

    def active_estimator_name(self) -> str:
        if self._active_estimator == EstimatorType.DISABLED:
            return "Disabled"
        if self._active_estimator == EstimatorType.CAST_TIME:
            return "CastTime"
        if self._active_estimator == EstimatorType.FORE_CAST:
            return "ForeCast"
        return "Unknown"

    def monitoring(self) -> None:
        if not self._active:
            logger.debug("Stop monitoring")
            return

        if self._pause:
            logger.debug("Pause monitoring")
            Timer(self._timing, self.monitoring).start()
            return

        # logger.debug("Monitoring every %.1f seconds" % self._timing)
        self._data_info = "Settings:\n" \
                          "- Estimator: %s\n" % self.active_estimator_name()
        if self._active_estimator != EstimatorType.DISABLED:
            self._data_info += "- Default draft: %.2f m\n" % self._default_draft
            self._data_info += "- Average depth: %.2f m\n" % self._avg_depth

        # Check if SIS is available and pinging
        if self._ssm.listeners.sis.is_alive():
            msg = self._retrieve_from_sis()
            if len(msg) > 0:
                if (self._counter % 1) == 0:
                    logger.debug("#%04d: monitor: %s" % (self._counter, msg))
                self._has_sis_data = True
                self._counter += 1

        if self._active_estimator == EstimatorType.CAST_TIME:
            logger.debug("Estimate using CastTime")
            self._estimate_with_cast_time()

        elif self._active_estimator == EstimatorType.FORE_CAST:
            logger.debug("Estimate using ForeCast")

        else:
            # logger.warning("Estimation disabled")
            pass

        Timer(self._timing, self.monitoring).start()

    def _estimate_with_cast_time(self) -> None:

        rows = self._ssm.db_timestamp_list()
        nr_rows = len(rows)
        if nr_rows == 0:
            logger.debug("The database is empty")
            return

        # logger.debug("DB has %d casts" % nr_rows)
        cur_datetime = rows[-1][0]
        cur_pk = rows[-1][1]
        if self._past_cast_time is None:

            self._past_cast_time = cur_datetime
            logger.debug("First cast from DB: #%d -> %s" % (cur_pk, self._past_cast_time))

            if nr_rows > 1:
                pre_cur_datetime = rows[-2][0]
                pre_cur_pk = rows[-2][1]

                pre_cur_ssp = self._ssm.db_retrieve_profile(pre_cur_pk)

                self._lock.acquire()

                if self._has_sis_data:
                    self._cur_draft = self._drafts[-1]
                    self._cur_tss = self._tsss[-1]
                    self._cur_depth = self._depths[-1]
                else:
                    self._cur_draft = self._default_draft
                    self._cur_tss = pre_cur_ssp.cur.interpolate_proc_speed_at_depth(self._default_draft)
                    self._cur_depth = self._avg_depth
                self._cur_time = pre_cur_datetime

                self._cast_time_updated = self._cast_time.update(tss_depth=self._cur_draft,
                                                                 tss_value=self._cur_tss,
                                                                 avg_depth=self._cur_depth,
                                                                 latest_cast_time=self._cur_time,
                                                                 latest_ssp=pre_cur_ssp)
                self._lock.release()

        else:
            if cur_datetime > self._past_cast_time:

                self._past_cast_time = cur_datetime
                logger.debug("New cast in DB: #%d -> %s" % (cur_pk, self._past_cast_time))

            else:

                logger.debug("No new cast in DB")
                return

        cur_ssp = self._ssm.db_retrieve_profile(cur_pk)

        self._lock.acquire()

        if self._has_sis_data:
            self._cur_draft = self._drafts[-1]
            self._cur_tss = self._tsss[-1]
            self._cur_depth = self._depths[-1]
        else:
            self._cur_draft = self._default_draft
            self._cur_tss = cur_ssp.cur.interpolate_proc_speed_at_depth(self._default_draft)
            self._cur_depth = self._avg_depth
        self._cur_time = cur_datetime

        self._cast_time_updated = self._cast_time.update(tss_depth=self._cur_draft,
                                                         tss_value=self._cur_tss,
                                                         avg_depth=self._cur_depth,
                                                         latest_cast_time=self._cur_time,
                                                         latest_ssp=cur_ssp)
        self._next_cast_time = self._cast_time.next_loc_cast_time
        self._lock.release()

    def _retrieve_from_sis(self) -> str:

        msg = str()

        # be sure that we have both navigation and depth datagrams
        if self._ssm.listeners.sis.nav is None:
            return str()
        if self._ssm.listeners.sis.nav_timestamp is None:
            return str()
        if (self._ssm.listeners.sis.nav_latitude is None) or (self._ssm.listeners.sis.nav_longitude is None):
            return str()
        if self._ssm.listeners.sis.xyz is None:
            return str()
        if self._ssm.listeners.sis.xyz_transducer_sound_speed is None:
            return str()

        # time stamp
        # - check to avoid to store the latest datagram after SIS is turned off
        if self._last_dgtime:
            if self._last_dgtime > self._ssm.listeners.sis.xyz.dg_time:
                return str()
        # - add string
        timestamp = self._ssm.listeners.sis.xyz.dg_time
        self._last_dgtime = timestamp
        msg += "%s, " % timestamp.strftime("%H:%M:%S.%f")

        # position
        # - latitude
        latitude = self._ssm.listeners.sis.nav_latitude
        if latitude >= 0:
            letter = "N"
        else:
            letter = "S"
        lat_min = float(60 * math.fabs(latitude - int(latitude)))
        lat_str = "%02d\N{DEGREE SIGN}%7.3f'%s" % (int(math.fabs(latitude)), lat_min, letter)
        # - longitude
        longitude = self._ssm.listeners.sis.nav_longitude
        if longitude < 0:
            letter = "W"
        else:
            letter = "E"
        lon_min = float(60 * math.fabs(longitude - int(longitude)))
        lon_str = "%03d\N{DEGREE SIGN}%7.3f'%s" % (int(math.fabs(longitude)), lon_min, letter)
        # - add string
        msg += "(%s, %s), " % (lat_str, lon_str)

        # - tss
        tss = self._ssm.listeners.sis.xyz_transducer_sound_speed
        msg += '%.2f m/s,  ' % tss
        # - draft
        draft = self._ssm.listeners.sis.xyz_transducer_depth
        msg += '%.1f m, ' % draft
        # - mean depth
        depth = self._ssm.listeners.sis.xyz_mean_depth
        msg += '%.1f m' % depth

        db = MonitorDb(projects_folder=self.output_folder, base_name=self.base_name)
        db.add_point(timestamp=timestamp, lat=latitude, long=longitude, tss=tss, draft=draft, avg_depth=depth)

        self._lock.acquire()

        self._times.append(timestamp)
        self._lats.append(latitude)
        self._longs.append(longitude)
        self._tsss.append(tss)
        self._drafts.append(draft)
        self._depths.append(depth)

        self._data_info += "\nSIS:\n" \
                           "- Total samples: %d\n" \
                           "- Timestamp: %s\n" \
                           "- Position: %.7f, %.7f\n" \
                           "- Surface sound speed: %.2f m\n" \
                           "- Transducer draft: %.2f m\n" \
                           "- Average swath depth: %.2f m\n" \
                           % (len(self._lats), timestamp.strftime("%d/%m/%y %H:%M:%S.%f"), longitude, latitude, tss,
                              draft, depth)

        self._lock.release()

        return msg

    def start_monitor(self, clear_data: Optional[bool] = True) -> None:
        if self._pause:
            logger.debug("Resume monitoring")
            self._pause = False
            return

        if clear_data:
            self.clear_data()
            self.base_name = self._ssm.current_project + "_" + datetime.datetime.now().strftime("%d%m%Y_%H%M%S")

        else:
            if self.base_name is None:
                self.base_name = self._ssm.current_project + "_" + datetime.datetime.now().strftime("%d%m%Y_%H%M%S")

        self._active = True
        self._pause = False
        logger.debug("Start monitoring")

        try:
            self.monitoring()
        except Exception as e:
            traceback.print_exc()
            logger.warning("monitoring issue: %s" % e)

    def clear_data(self) -> None:
        self._times.clear()
        self._lats.clear()
        self._longs.clear()
        self._tsss.clear()
        self._drafts.clear()
        self._depths.clear()
        self._data_info = str()
        self._counter = 0
        self.base_name = None

    def pause_monitor(self) -> None:
        self._active = True
        self._pause = True

    def stop_monitor(self) -> None:
        self._active = False
        self._pause = False

    def nr_of_samples(self) -> int:
        self._lock.acquire()
        nr = len(self._times)
        self._lock.release()
        return nr

    def find_next_idx_in_time(self, ts: datetime.datetime) -> int:
        time_idx = len(self._times) - 1
        for _idx, _time in enumerate(self._times):
            if ts < _time:
                return _idx
        return time_idx

    def lonlat_casts(self, min_time: datetime.datetime, max_time: datetime.datetime) -> tuple:

        rows = self._ssm.db_timestamp_list()
        nr_rows = len(rows)
        if nr_rows == 0:
            logger.debug("The database is empty")
            return list(), list()

        lons = list()
        lats = list()

        for row in rows:
            cur_datetime = row[0]
            if (cur_datetime < min_time) or (cur_datetime > max_time):
                continue

            cur_pk = row[1]
            cur_ssp = self._ssm.db_retrieve_profile(cur_pk)
            lons.append(cur_ssp.cur.meta.longitude)
            lats.append(cur_ssp.cur.meta.latitude)

        return lons, lats

    def add_kongsberg_data(self, filenames: list) -> None:

        for filename in filenames:

            if not os.path.exists(filename):
                raise RuntimeError("The passed db to merge does not exist")

            kng = EmSeries(file_input=filename)
            logger.debug(kng)

            output_folder = os.path.abspath(os.path.dirname(filename))
            basename = os.path.splitext(os.path.basename(filename))[0]
            if self.base_name is None:
                self.base_name = basename
            logger.debug("db -> output: %s, basename: %s" % (output_folder, basename))

            output_db = MonitorDb(projects_folder=self.output_folder, base_name=self.base_name)
            logger.debug("output db: %s" % output_db)

            input_times = kng.timestamps
            output_times, _ = output_db.timestamp_list()

            for idx, input_time in enumerate(input_times):

                if input_time in output_times:

                    logger.debug("An entry with the same timestamp is in the output db! -> Skipping entry import")

                else:

                    success = output_db.add_point(timestamp=kng.timestamps[idx],
                                                  lat=kng.lats[idx],
                                                  long=kng.longs[idx],
                                                  tss=kng.tsss[idx],
                                                  draft=kng.drafts[idx],
                                                  avg_depth=kng.avg_depths[idx])
                    if not success:
                        logger.warning("issue in importing point with timestamp: %s" % input_time)

                # insert the new data in chronological order
                self._lock.acquire()

                if input_time not in self._times:
                    insert_idx = self.find_next_idx_in_time(input_time)

                    try:
                        self._times.insert(insert_idx, kng.timestamps[insert_idx])
                        self._lats.insert(insert_idx, kng.lats[insert_idx])
                        self._longs.insert(insert_idx, kng.longs[insert_idx])
                        self._tsss.insert(insert_idx, kng.tsss[insert_idx])
                        self._drafts.insert(insert_idx, kng.drafts[insert_idx])
                        self._depths.insert(insert_idx, kng.avg_depths[insert_idx])

                    except IndexError:
                        logger.error("invalid index: %d, length: %d" % (insert_idx, len(self._times)))

                self._lock.release()

    def add_db_data(self, filenames: list) -> None:

        for filename in filenames:

            if not os.path.exists(filename):
                raise RuntimeError("The passed db to merge does not exist")

            output_folder = os.path.abspath(os.path.dirname(filename))
            basename = os.path.splitext(os.path.basename(filename))[0]
            logger.debug("db: %s, %s" % (output_folder, basename))

            if self.base_name is None:
                self.base_name = basename

            load_in_db = True

            if (output_folder == self.output_folder) and (basename == self.base_name):
                logger.debug("Input and output are the same! -> Just loading data")
                load_in_db = False
            # print(output_folder, self.output_folder, basename, self.base_name)

            input_db = MonitorDb(projects_folder=output_folder, base_name=basename)
            # logger.debug("input db: %s" % input_db)

            output_db = None
            if load_in_db:
                output_db = MonitorDb(projects_folder=self.output_folder, base_name=self.base_name)
                # logger.debug("output db: %s" % output_db)
                output_times, _ = output_db.timestamp_list()
            else:
                output_times = list()

            input_times, input_ids = input_db.timestamp_list()
            if len(input_times) == 0:
                logger.info("Input db is empty! -> Skipping db file")
                continue

            for idx, input_time in enumerate(input_times):

                if input_time in output_times:
                    logger.debug("An entry with the same timestamp is in the output db! -> Skipping entry import")
                    continue

                timestamp, long, lat, tss, draft, avg_depth = input_db.point_by_id(input_ids[idx])
                if load_in_db:
                    success = output_db.add_point(timestamp=timestamp, lat=lat, long=long, tss=tss,
                                                  draft=draft, avg_depth=avg_depth)
                    if not success:
                        logger.warning("issue in importing point with timestamp: %s" % input_time)

                # insert the new data in chronological order
                self._lock.acquire()

                insert_idx = self.find_next_idx_in_time(input_time)
                self._times.insert(insert_idx, timestamp)
                self._lats.insert(insert_idx, lat)
                self._longs.insert(insert_idx, long)
                self._tsss.insert(insert_idx, tss)
                self._drafts.insert(insert_idx, draft)
                self._depths.insert(insert_idx, avg_depth)

                self._lock.release()

    def export_surface_speed_points_shapefile(self) -> None:
        db = MonitorDb(projects_folder=self.output_folder, base_name=self.base_name)
        db.export.export_surface_speed_points(output_folder=self.output_folder)

    def export_surface_speed_points_kml(self) -> None:
        db = MonitorDb(projects_folder=self.output_folder, base_name=self.base_name)
        db.export.export_surface_speed_points(output_folder=self.output_folder,
                                              ogr_format=GdalAux.ogr_formats['KML'])

    def export_surface_speed_points_csv(self) -> None:
        db = MonitorDb(projects_folder=self.output_folder, base_name=self.base_name)
        db.export.export_surface_speed_points(output_folder=self.output_folder,
                                              ogr_format=GdalAux.ogr_formats['CSV'])

    def export_surface_speed_points_geotiff(self) -> None:
        db = MonitorDb(projects_folder=self.output_folder, base_name=self.base_name)
        db.export.rasterize_surface_speed_points(output_folder=self.output_folder)

    @classmethod
    def calc_plot_good_range(cls, data: list) -> tuple:

        min_value = min(data)
        max_value = max(data)
        nr_samples = len(data)
        range_value = max_value - min_value

        if (nr_samples < 20) or (range_value < 5.0):
            min_plot = min_value - 0.1
            max_plot = max_value + 0.1

        else:
            def median_mad(in_data):
                med_value = statistics.median(in_data)
                mad_value = statistics.median([abs(in_value - med_value) for in_value in in_data])

                return med_value, mad_value

            med, mad = median_mad(in_data=data)
            logger.debug("median: %s, mad: %s" % (med, mad))

            min_plot = med - 3 * mad
            max_plot = med + 3 * mad

        return min_plot, max_plot

    def __repr__(self) -> str:
        msg = "<%s>\n" % self.__class__.__name__

        msg += "  <Active estimator: %s>\n" % self._active_estimator

        return msg
