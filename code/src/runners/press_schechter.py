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

    def tasks(self, hf: str):
        logger = logging.getLogger(
            __name__ + "." +
            PressSchechterRunner.__name__ + "." +
            self.tasks.__name__)

        ds = self._ds_cache.load(hf)
        z = ds.current_redshift
        logger.info(f"Redshift is: {z}")

        rb = rho_bar.RhoBar(self._data, type=self._type)
        std_dev = standard_deviation.StandardDeviation(
            self._data, type=self._type)
        mf = mass_function.MassFunction(self._data, type=self._type)

        # =============================================================
        # RHO BAR 0
        # =============================================================

        rho_0 = rb.rho_bar_0(hf)
        if rho_0 is None:
            logger.warning("Could not calculate rho bar 0!")
            return
        rho_0 = rho_0.to("Msun/h / (Mpc/h)**3")

        logger.info(f"Simulation average density is: {rho_0}")

        # =================================================================
        # PRESS SCHECHTER MASS FUNCTION
        # =================================================================

        press_schechter = self._cache[hf,
                                      self._type.value, PRESS_SCHECHTER_KEY, z].val

        needs_recalc = press_schechter is None
        needs_recalc |= not self._conf.caches.use_press_schechter_cache
        if needs_recalc:
            logger.debug(
                f"No press-schechter values cached for '{hf}' data set, caching...")  # noqa: E501

            all_mass = mf.cache_total_mass_function(hf)
            all_mass = all_mass.to("Msun / h")
            std_dev = np.std(all_mass)

            frac = np.abs(np.log(std_dev) / np.log(all_mass))

            press_schechter = np.sqrt(2 / np.pi) * (rho_0 / all_mass**2) * DELTA_CRIT / \
                std_dev * frac * np.exp(-DELTA_CRIT / (2 * std_dev**2))

            if isinstance(press_schechter, unyt.unyt_array):
                logger.debug(
                    f"Press-Schechter mass function units are: {press_schechter.units}")

            self._cache[hf, self._type.value,
                        PRESS_SCHECHTER_KEY, z] = press_schechter

        else:
            logger.debug("Using cached press schechter values...")

        # =================================================================
        # PLOTTING
        # =================================================================
        sim_name = self._data.sim_name
        min_mass = self._ds_cache.min_mass(hf)

        ps_hist, ps_bins = mf.create_histogram(press_schechter)

        plotter = plotting.Plotter(self._data, self._type)
        plotter.press_schechter(z, ps_hist, ps_bins, sim_name, min_mass)

        # =============================================================
        # COMPARISON OF PS MASS FUNCTION WITH SIMULATION
        # =============================================================

        for radius in self._conf.radii:

            # Get the mass samples
            ms = mf.sample_masses(hf, radius)

            # Get the histogram and scale it
            hist, bins = mf.create_histogram(ms)
            a = 1 / (1+z)
            V = 4/3 * np.pi * (a*radius)**3

            hist = hist / V

            # Plot
            plotter.press_schechter_comparison(z, radius, hist, bins,
                                               ps_hist, ps_bins, sim_name)


def main(args):
    ps_runner = PressSchechterRunner(args)
    ps_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
