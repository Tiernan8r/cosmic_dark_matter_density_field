#!/usr/bin/env python3
import logging
import logging.config
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import numpy as np
import unyt
from src import runner
from src.calc import mass_function, rho_bar, standard_deviation
from src.const.constants import PRESS_SCHECHTER_KEY
from src.plot import plotting

DELTA_CRIT = 1.686


class PressSchechterRunner(runner.Runner):

    def tasks(self, rck: str):
        logger = logging.getLogger(
            __name__ + "." + PressSchechterRunner.__name__ + "." + self.tasks.__name__)

        ds = self._ds_cache.load(rck)
        z = ds.current_redshift
        logger.info(f"Redshift is: {z}")

        rb = rho_bar.RhoBar(self._data)
        std_dev = standard_deviation.StandardDeviation(self._data)
        mf = mass_function.MassFunction(self._data)

        # =============================================================
        # RHO BAR 0
        # =============================================================

        rho_0 = rb.rho_bar_0(rck)
        if rho_0 is None:
            logger.warning(f"Could not calculate rho bar 0!")
            return

        logger.info(f"Simulation average density is: {rho_0}")

        # =================================================================
        # PRESS SCHECHTER MASS FUNCTION
        # =================================================================

        press_schechter = self._cache[rck, PRESS_SCHECHTER_KEY, z].val
        if press_schechter is None or not self._conf.caches.use_press_schechter_cache:
            logger.debug(
                f"No press-schechter values cached for '{rck}' data set, caching...")

            std_dev_map = std_dev.std_dev_func_mass(rck)
            if std_dev_map is None:
                logger.warn(
                    f"No standard deviations mapped for this redshift, stopping...")
                return

            press_schechter = {}

            masses = np.array(sorted(std_dev_map.keys()))
            std_devs = np.array([std_dev_map[k] for k in masses])

            frac = np.abs(np.log(std_devs) / np.log(masses))

            ps = np.sqrt(2 / np.pi) * (rho_0 / masses**2) * DELTA_CRIT / \
                std_devs * frac * np.exp(-DELTA_CRIT / (2 * std_devs**2))

            if isinstance(ps, unyt.unyt_array):
                logger.debug(
                    f"Press-Schechter mass function units are: {ps.units}")

            # Match up the entries into the dictionary
            for i in range(len(masses)):
                press_schechter[masses[i]] = ps[i]

            self._cache[rck, PRESS_SCHECHTER_KEY, z] = press_schechter

        else:
            logger.debug("Using cached press schechter values...")

        # =================================================================
        # PLOTTING
        # =================================================================
        sim_name = self._data.sim_name

        plotter = plotting.Plotter(self._data)
        plotter.press_schechter(z, press_schechter, sim_name)

        # =============================================================
        # COMPARISON OF PS MASS FUNCTION WITH SIMULATION
        # =============================================================

        for radius in self._conf.radii:

            # Get the mass samples
            ms = mf.sample_masses(rck, radius)

            # Get the histogram and scale it
            hist, bins = mf.create_histogram(ms)
            a = 1 / (1+z)
            V = 4/3 * np.pi * (a*radius)**3

            hist = hist / V

            # Plot
            plotter.press_schechter_comparison(z, radius, hist, bins,
                                 press_schechter, sim_name)


def main(args):
    ps_runner = PressSchechterRunner(args)
    ps_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
