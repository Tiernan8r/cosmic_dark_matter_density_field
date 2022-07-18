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
from src import runner
from src import units as u
from src.calc import (mass_function, press_schechter, rho_bar,
                      standard_deviation)
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
        ps = press_schechter.PressSchechter(self._data, type=self._type)

        # =============================================================
        # RHO BAR 0
        # =============================================================

        rho_0 = rb.rho_bar_0(hf)
        if rho_0 is None:
            logger.warning("Could not calculate rho bar 0!")
            return

        rho_0 = rho_0.to(u.density(ds))

        logger.info(f"Simulation average density is: {rho_0}")

        for radius in self._conf.radii:
            # =================================================================
            # PRESS SCHECHTER MASS FUNCTION
            # =================================================================

            masses, press = ps.mass_function(hf, radius)

            # =================================================================
            # PLOTTING
            # =================================================================
            sim_name = self._data.sim_name
            min_mass = self._ds_cache.min_mass(hf, mass_units=u.mass(ds))

            # ps_hist, ps_bins = mf.create_histogram(press_schechter)

            plotter = plotting.Plotter(self._data, self._type)
            plotter.press_schechter(z, masses, press, sim_name, min_mass)

            # =============================================================
            # COMPARISON OF PS MASS FUNCTION WITH SIMULATION
            # =============================================================

            # Get the mass samples
            ms = mf.sample_masses(hf, radius)

            # Get the histogram and scale it
            hist, bins = mf.create_histogram(ms)
            a = 1 / (1+z)
            V = 4/3 * np.pi * (a*radius)**3

            hist = hist / V

            # Plot
            plotter.press_schechter_comparison(z, radius, hist, bins,
                                               masses, press, sim_name)


def main(args):
    ps_runner = PressSchechterRunner(args)
    ps_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
