cimport numpy
import numpy
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

from hyo2.sdm4.lib.estimate.abstractestimator import AbstractEstimator, EstimatorType, EstimationModes
from hyo2.ssm2.lib.profile.ray_tracing.tracedprofile import TracedProfile
from hyo2.ssm2.lib.profile.ray_tracing.diff_tracedprofiles import DiffTracedProfiles
from hyo2.ssm2.lib.profile.ray_tracing.plot_tracedprofiles import PlotTracedProfiles


class CastTime(AbstractEstimator):

    def __init__(self,
                 initial_interval=100.0, minimum_interval=10.0, maximum_interval=300.0,
                 fixed_allowable_error=0.3, variable_allowable_error=0.005,
                 half_swath_angle=70.0
                 ):
        super().__init__()
        self._type = EstimatorType.CAST_TIME
        self._mode = EstimationModes.UNKNOWN

        # store the user-defined settings
        self._cur_interval = initial_interval
        self._minimum_interval = minimum_interval
        self._maximum_interval = maximum_interval
        self._fixed_allowable_error = fixed_allowable_error
        self._variable_allowable_error = variable_allowable_error
        self._half_swath_angle = half_swath_angle

        self._next_loc_cast_time = None
        self._profiles = list()
        self._info_message = "N/A"

        # diff traced profiles
        self._d = None

        # plotting stuff
        self._plot = None
        self._plotting_mode = False
        self.old_idx = -2
        self.new_idx = -1
        self._latest_plotted_cast = None

        # recalculate stuff
        self._last2_tss_depth = None
        self._last2_tss_value = None
        self._last2_avg_depth = None
        self._last2_latest_cast_time = None
        self._last2_latest_ssp = None
        self._last2_cur_interval = None
        self._last_tss_depth = None
        self._last_tss_value = None
        self._last_avg_depth = None
        self._last_latest_cast_time = None
        self._last_latest_ssp = None
        self._last_cur_interval = None

    @property
    def profiles(self):
        return self._profiles

    @property
    def mode(self):
        return self._mode

    @property
    def current_interval(self):
        return self._cur_interval

    @current_interval.setter
    def current_interval(self, value):
        self._cur_interval = value

    @property
    def minimum_interval(self):
        return self._minimum_interval

    @minimum_interval.setter
    def minimum_interval(self, value):
        self._minimum_interval = value

    @property
    def maximum_interval(self):
        return self._maximum_interval

    @maximum_interval.setter
    def maximum_interval(self, value):
        self._maximum_interval = value

    @property
    def fixed_allowable_error(self):
        return self._fixed_allowable_error

    @fixed_allowable_error.setter
    def fixed_allowable_error(self, value):
        self._fixed_allowable_error = value

    @property
    def variable_allowable_error(self):
        return self._variable_allowable_error

    @variable_allowable_error.setter
    def variable_allowable_error(self, value):
        self._variable_allowable_error = value

    @property
    def half_swath_angle(self):
        return self._half_swath_angle

    @half_swath_angle.setter
    def half_swath_angle(self, value):
        self._half_swath_angle = value

    @property
    def next_loc_cast_time(self):
        return self._next_loc_cast_time

    @property
    def plotting_mode(self):
        return self._plotting_mode

    @plotting_mode.setter
    def plotting_mode(self, value):
        self._plotting_mode = value

    @property
    def info_message(self):
        return self._info_message

    @info_message.setter
    def info_message(self, value):
        self._info_message = value

    def recalculate(self):
        if (self._last_tss_depth is None) or (self._last_tss_value is None) or (self._last_avg_depth is None) \
                or (self._last_latest_cast_time is None) or (self._last_latest_ssp is None):
            logger.info("nothing stored to be recalculated")
            return

        self._profiles.clear()
        self._latest_plotted_cast = None

        # required to avoid that the (last - 1) values becomes the last
        last_tss_depth = self._last_tss_depth
        last_tss_value = self._last_tss_value
        last_avg_depth = self._last_avg_depth
        last_latest_cast_time = self._last_latest_cast_time
        last_latest_ssp = self._last_latest_ssp
        last_cur_interval = self._last_cur_interval

        if self._last2_tss_depth and self._last2_tss_value and self._last2_avg_depth \
                and self._last2_latest_cast_time and self._last2_latest_ssp:
            logger.debug("recalculating last profile - 1")
            self._cur_interval = self._last2_cur_interval
            success = self.update(tss_depth=self._last2_tss_depth, tss_value=self._last2_tss_value,
                                  avg_depth=self._last2_avg_depth, latest_cast_time=self._last2_latest_cast_time,
                                  latest_ssp=self._last2_latest_ssp)
            if not success:
                logger.info("issue with using the last profile - 1")
                return
        else:
            self._cur_interval = last_cur_interval

        logger.debug("recalculating last profile")
        self.update(tss_depth=last_tss_depth, tss_value=last_tss_value, avg_depth=last_avg_depth,
                    latest_cast_time=last_latest_cast_time, latest_ssp=last_latest_ssp)

    def update(self, tss_depth, tss_value, avg_depth, latest_cast_time, latest_ssp):

        # stored for recalculation
        # * last cast - 1
        self._last2_tss_depth = self._last_tss_depth
        self._last2_tss_value = self._last_tss_value
        self._last2_avg_depth = self._last_avg_depth
        self._last2_latest_cast_time = self._last_latest_cast_time
        self._last2_latest_ssp = self._last_latest_ssp
        self._last2_cur_interval = self._last_cur_interval
        # * last cast
        self._last_tss_depth = tss_depth
        self._last_tss_value = tss_value
        self._last_avg_depth = avg_depth
        self._last_latest_cast_time = latest_cast_time
        self._last_latest_ssp = latest_ssp
        self._last_cur_interval = self._cur_interval

        logger.debug("Plotting mode: %s" % self._plotting_mode)

        # check time of the lasted profile
        time_delta = (latest_cast_time - latest_ssp.cur.meta.utc_time).total_seconds() / 60.0
        logger.debug("Ping time since the latest profile: %.1f mins" % time_delta)
        if time_delta > self._cur_interval:
            logger.info("Latest profile is too old to be used for estimation")
            return False

        # skip calculation for existing profiles
        if len(self._profiles) > 0:
            if latest_ssp.cur.meta.utc_time == self._profiles[-1].date_time:
                logger.info("Skipping existing profile")
                return False

        logger.debug("using tss: %.1f m/s at %.1f m" % (tss_value, tss_depth))
        logger.debug("using avg depth: %.1f m" % (avg_depth,))
        logger.debug("using latest cast time: %s" % (latest_cast_time,))

        # populate ad-hoc sound speed profile
        profile = TracedProfile(ssp=latest_ssp.cur,
                                half_swath=self._half_swath_angle, avg_depth=avg_depth,
                                tss_depth=tss_depth, tss_value=tss_value )
        if len(profile.rays[0][0]) < 2:
            logger.warning("latest profile (%s) too short -> skipping" % (latest_ssp.cur.meta.utc_time, ))
            return False
        self._profiles.append(profile)
        logger.debug("using ray-traced profile: %s" % profile)

        # update interval
        if len(self._profiles) == 1:

            rr = self._cur_interval
            rr_alt = self._cur_interval
            pr = self._cur_interval
            self._info_message = str()

        else:  # len(self._profiles) > 1

            # indices of the latest two profiles
            self.new_idx = len(self._profiles) - 1
            self.old_idx = self.new_idx - 1

            # compare the latest two profiles
            max_r, rms_r, d, pr, max_rate, t, rr = self._profile_comparison()

            max_rate_alt = t / (max_r / self._cur_interval)
            rr_alt = self._find_rate(max_r, t, max_rate_alt, self._cur_interval,
                                     self._maximum_interval, self._minimum_interval)

            msg = "Time between latest two casts: %.0f mins" % (pr, )
            self._info_message += "\n" + msg + "\n"
            msg = "Previous recommended interval: %.0f mins" % (self._cur_interval, )
            self._info_message += msg + "\n"

        if pr >= self._cur_interval:

            self._cur_interval = rr_alt

        else:  # if pr < self._initial_interval:
            self._cur_interval = rr

        msg = "Current recommended interval: %.0f mins" % self._cur_interval
        self._info_message += msg + "\n"
        logger.debug(msg)

        epoch = time.mktime(self._profiles[-1].date_time.timetuple())
        offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)

        beg_gmt = self._profiles[-1].date_time
        beg_loc = beg_gmt + offset
        msg = "Latest cast time:\n- %s [GMT]\n- %s [PC time]" % (beg_gmt, beg_loc)
        self._info_message += "\n" + msg + "\n"

        end_gmt = self._profiles[-1].date_time + timedelta(minutes=self._cur_interval)
        end_loc = end_gmt + offset
        self._next_loc_cast_time = end_loc
        msg = "Next recommended cast time:\n- %s [GMT]\n- %s [PC time]" % (end_gmt, end_loc)
        self._info_message += msg + "\n"

        logger.debug(msg=msg)

        if len(self._profiles) == 0:
            return False

        return True

    def _total_hours_elapsed(self):

        total_hours_elapsed = list()

        base = self._profiles[0].date_time

        for idx in range(0, len(self._profiles)):

            delta_dt = self._profiles[idx].date_time - base
            delta_hours = delta_dt.total_seconds() / 3600.0
            total_hours_elapsed.append(delta_hours)

        return total_hours_elapsed

    def _profile_difference(self):

        self._d = DiffTracedProfiles(old_tp=self._profiles[self.old_idx],
                                        new_tp=self._profiles[self.new_idx])
        self._d.fixed_allowable_error = self.fixed_allowable_error  # optional
        self._d.variable_allowable_error = self.variable_allowable_error  # optional
        self._d.calc_diff()
        depth_output = max(self._d.new_rays[-1][2])

        # TODO: Calculate distance error
        old_x_ends = [ray[1][-1] for ray in self._d.old_rays]
        new_x_ends = [ray[1][-1] for ray in self._d.new_rays]
        old_z_ends = numpy.array([ray[2][-1] for ray in self._d.old_rays])
        new_z_ends = numpy.array([ray[2][-1] for ray in self._d.new_rays])

        z_diff = new_z_ends - old_z_ends

        max_refract = max(abs(new_z_ends - old_z_ends))
        rms_refract = ((sum((abs(new_z_ends - old_z_ends)) ** 2))
                       / (len(new_z_ends))) ** .5
        tolerance = (depth_output * self.variable_allowable_error) + self.fixed_allowable_error

        return z_diff, max_refract, rms_refract, tolerance, depth_output

    def _profile_comparison(self):

        total_hours_elapsed = self._total_hours_elapsed()
        z_diff, max_refract, rms_refract, tolerance, depth_output = self._profile_difference()

        previous_rate = 60 * (total_hours_elapsed[self.new_idx] - total_hours_elapsed[self.old_idx])
        if previous_rate == 0:
            previous_rate = 1.0

        max_rate = (tolerance / (max_refract / previous_rate))

        recommended_rate = self._find_rate(max_refract, tolerance, max_rate, previous_rate,
                                           self._maximum_interval, self._minimum_interval)

        logger.debug("Outer Beam Refraction Error: %.2f m" % max_refract)
        logger.debug("Maximum Allowable Error: %.2f m" % tolerance)

        abs_seafloor_diff = abs(z_diff)

        count = 0
        steady_count = 0
        relax_count = 0
        for m in range(0, len(abs_seafloor_diff)):
            if abs_seafloor_diff[m] < tolerance:
                count = count + 1
            if abs_seafloor_diff[m] < ((2.0 / 3.0) * tolerance):
                steady_count = steady_count + 1
            if abs_seafloor_diff[m] < ((1.0 / 3.0) * tolerance):
                relax_count = relax_count + 1

        self._info_message = "CastTime Analysis\n\n"

        msg = "For a \xb1%d\xb0 swath,\n" \
              "- \xb1%d\xb0 within full allowable error (%.2f m)\n" \
              "- \xb1%d\xb0 within  2/3 allowable error (%.2f m)\n" \
              "- \xb1%d\xb0 within  1/3 allowable error (%.2f m)" \
              % (len(self._profiles[0].rays) - 1,
                 count - 1, tolerance,
                 steady_count - 1, tolerance * (2.0/3.0),
                 relax_count - 1, tolerance * (1.0/3.0))
        self._info_message += "%s\n" % msg
        logger.debug(msg=msg)

        if max_refract >= (2.0/3.0) * tolerance:

            self._mode = EstimationModes.PANIC
            msg = "Current mode: PANIC"

        elif (max_refract < (2.0 / 3.0) * tolerance) and (max_refract >= (1.0/3.0) * tolerance):

            self._mode = EstimationModes.STEADY
            msg = "Current mode: STEADY"

        elif max_refract < (1.0/3.0)*tolerance:

            self._mode = EstimationModes.RELAX
            msg = "Current mode: RELAX"

        self._info_message += "%s\n" % msg
        logger.info(msg)

        return max_refract, rms_refract, depth_output, \
               previous_rate, max_rate, tolerance, recommended_rate

    def _find_rate(self, max_refract, tolerance, max_rate, previous_rate, upper_bound, lower_bound):

        recommended_rate = 0

        if max_refract >= ((2.0 / 3.0) * tolerance):

            recommended_rate = 0.5 * max_rate

        elif ((2.0 / 3.0) * tolerance) > max_refract >= ((1.0 / 3.0) * tolerance):

            recommended_rate = previous_rate

        elif max_refract < ((1.0 / 3.0) * tolerance):

            added_time = previous_rate * 0.15
            if added_time < 1.0:
                added_time = 1.0
            recommended_rate = previous_rate + added_time

        if recommended_rate > ((2.0 / 3.0) * max_rate):

            recommended_rate = (0.5 * max_rate)

        if recommended_rate > upper_bound:

            recommended_rate = upper_bound

        if recommended_rate < lower_bound:

            recommended_rate = lower_bound

        return recommended_rate

    def plotting_analysis(self, current_time, label1=None, label2=None, legend_loc=None):

        logger.info("plotting required")

        if self._d is None:
            return

        if self._latest_plotted_cast is None:
            self._latest_plotted_cast = current_time
        else:
            if current_time <= self._latest_plotted_cast:
                return
            else:
                self._latest_plotted_cast = current_time

        self._plot = PlotTracedProfiles(diff_tps=self._d)
        self._plot.make_comparison_plots()

    def __repr__(self):
        msg = super().__repr__() + "\n"

        msg += "  <initial interval: %.1f>\n" % self._cur_interval
        msg += "  <lower interval: %.1f>\n" % self._minimum_interval
        msg += "  <upper interval: %.1f>\n" % self._maximum_interval

        msg += "  <fixed allowable error: %.1f>\n" % self._fixed_allowable_error
        msg += "  <variable allowable error: %.4f>\n" % self._variable_allowable_error

        msg += "  <half swath angle: %.1f>\n" % self._half_swath_angle

        msg += "  <debug mode: %s>\n" % self._plotting_mode

        return msg
