import logging
import os
import statistics
from datetime import datetime, timezone

import numpy as np

logger = logging.getLogger(__name__)


class EmSeries:
    """Class that provides an interface to a SQLite db with Sound Speed data"""

    def __init__(self, file_input: str) -> None:
        if not os.path.exists(file_input):
            raise RuntimeError("The passed data file does not exist: %s" % file_input)
        self._file_input: str = file_input

        self._pos_timestamps = None
        self._pos_lats = None
        self._pos_longs = None
        self._pos_cogs = None
        self._pos_sogs = None
        self._read_pos()

        self._xyz_timestamps = None
        self._xyz_tsss = None
        self._xyz_drafts = None
        self._xyz_avg_depths = None
        self._read_xyz()

        self._timestamps = list()
        self._lats = list()
        self._longs = list()
        self._tsss = list()
        self._drafts = list()
        self._avg_depths = list()
        self._calc_outputs()

    @property
    def timestamps(self):
        return self._timestamps

    @property
    def lats(self):
        return self._lats

    @property
    def longs(self):
        return self._longs

    @property
    def tsss(self):
        return self._tsss

    @property
    def drafts(self):
        return self._drafts

    @property
    def avg_depths(self):
        return self._avg_depths

    def _read_pos(self) -> None:

        try:
            from hyo2.rawdata.info.kng.kng_u._kng_u_position_info import KngU_PositionInfo
        except ImportError as e:
            logger.error("Could not import KngU_XyzInfo: %s" % e, exc_info=True)
            return

        info = KngU_PositionInfo()
        # noinspection PyArgumentList
        info.read(self._file_input)

        # self._pos_timestamps = [datetime.utcfromtimestamp(val) for val in info.timestamps]
        self._pos_timestamps = list(info.timestamps)
        # logger.debug("timestamps: %s" % self._pos_timestamps)

        self._pos_lats = list(info.latitudes)
        # logger.debug("lats: %s" % self._pos_lats)
        self._pos_longs = list(info.longitudes)
        # logger.debug("longs: %s" % self._pos_longs)

        self._pos_cogs = list(info.sogs)
        # logger.debug("SOGs: %s" % self._pos_cogs)
        self._pos_sogs = list(info.cogs)
        # logger.debug("COGs: %s" % self._pos_sogs)

    def _read_xyz(self) -> None:

        try:
            from hyo2.rawdata.info.kng.kng_u._kng_u_xyz_info import KngU_XyzInfo
        except ImportError as e:
            logger.error("Could not import KngU_XyzInfo: %s" % e, exc_info=True)
            return

        info = KngU_XyzInfo()
        # noinspection PyArgumentList
        info.read(self._file_input)

        # self._xyz_timestamps = [datetime.utcfromtimestamp(val) for val in info.timestamps]
        self._xyz_timestamps = list(info.timestamps)
        # logger.debug("timestamps: %s" % self._xyz_timestamps)

        self._xyz_tsss = list(info.tdr_sound_speeds)
        # logger.debug("TSSs: %s" % self._xyz_tsss)
        self._xyz_drafts = list(info.tdr_depths)
        # logger.debug("drafts: %s" % self._xyz_drafts)

        self._xyz_avg_depths = [statistics.mean(ds) for ds in info.depths]
        # logger.debug("avg depths: %s" % self._xyz_avg_depths)

    def _calc_outputs(self) -> None:

        fit_lats = np.polyfit(self._pos_timestamps, self._pos_lats, 1)
        line_lats = np.poly1d(fit_lats)
        fit_longs = np.polyfit(self._pos_timestamps, self._pos_longs, 1)
        line_longs = np.poly1d(fit_longs)

        latest_xyz_timestamp = None

        for xyz_idx, xyz_timestamp in enumerate(self._xyz_timestamps):

            # decimate output up to a sample each 3 seconds
            if latest_xyz_timestamp is not None:
                if (xyz_timestamp - latest_xyz_timestamp) < 3:
                    continue
                else:
                    latest_xyz_timestamp = xyz_timestamp
            else:
                latest_xyz_timestamp = xyz_timestamp

            self._timestamps.append(datetime.fromtimestamp(xyz_timestamp, tz=timezone.utc))
            self._lats.append(line_lats(xyz_timestamp))
            self._longs.append(line_longs(xyz_timestamp))

            self._tsss.append(self._xyz_tsss[xyz_idx])
            self._drafts.append(self._xyz_drafts[xyz_idx])
            self._avg_depths.append(self._xyz_avg_depths[xyz_idx])

    def __repr__(self) -> str:
        msg = "<%s>\n" % self.__class__.__name__

        msg += "  <file input: %s>\n" % self._file_input

        if self._pos_timestamps:
            msg += "  <position samples: %d>\n" % len(self._pos_timestamps)

        if self._xyz_timestamps:
            msg += "  <xyz samples: %d>\n" % len(self._xyz_timestamps)

        msg += "  <interpolated samples: %d>\n" % len(self._timestamps)

        return msg
