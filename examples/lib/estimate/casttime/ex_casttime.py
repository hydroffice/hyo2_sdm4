import pyximport
pyximport.install()
import Cython.Compiler.Options
Cython.Compiler.Options.annotate = True

import logging
import os

from hyo2.abc2.lib.logging import set_logging
from hyo2.abc2.lib.testing import Testing
from hyo2.sdm4.lib.estimate.casttime.casttime import CastTime
from hyo2.ssm2.lib.db.db import ProjectDb

logger = logging.getLogger(__name__)
set_logging()

ct = CastTime()
ct.plotting_mode = True
logger.debug(ct)

data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir, os.pardir))
testing = Testing(root_folder=data_folder)

db_path = testing.input_test_files(ext=".db")[-1]
logger.debug("db path: %s" % db_path)
db = ProjectDb(projects_folder=os.path.dirname(db_path), project_name=os.path.splitext(os.path.basename(db_path))[0])
# logger.debug("db: %s" % db)

rows = db.timestamp_list()
logger.debug("number of profiles: %s" % len(rows))
tss_depth = 0.5
tss_value = 1544.0
avg_depth = 50.0
for idx, row in enumerate(rows):

    logger.debug(" - %s: %s [key: %s]" % (idx, row[0], row[1]))

    # if idx not in [0, 4, 8]:
    #     continue

    ssp = db.profile_by_pk(row[1])
    # logger.debug(" %s" % profile)
    # ssp_depth = ssp.cur.proc.depth[ssp.cur.proc_valid]
    # ssp_speed = ssp.cur.proc.speed[ssp.cur.proc_valid]
    # logger.debug("   - depth: %s" % ssp_depth)
    # logger.debug("   - speed: %s" % ssp_speed)

    latest_ping = ssp.cur.meta.utc_time
    # tss_depth, tss_value, avg_depth, latest_cast_time, latest_ssp
    ct.update(tss_depth, tss_value, avg_depth, latest_ping, ssp)

    logger.debug("%s" % ct.info_message)
    ct.plotting_analysis(current_time=latest_ping, label1="profile #1", label2="profile #2", legend_loc="upper left")
