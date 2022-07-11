#!/usr/bin/env python3
import logging
import logging.config
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from src import runner
from src.calc import mass_function, overdensity, rho_bar, standard_deviation
from src.plot import plotting


class MainRunner(runner.Runner):

    def tasks(self, rck: str):
        logger = logging.getLogger(self.tasks.__name__)

        logger.debug(f"Working on rockstar file '{rck}'")

        logger.debug("Calculating total halo mass function")

        mass_fn = mass_function.MassFunction(self._data)
        rb = rho_bar.RhoBar(self._data)
        plotter = plotting.Plotter(self._data)

        # =================================================================
        # TOTAL MASS FUNCTION
        # =================================================================
        ds = self._ds_cache.load(rck)
        z = ds.current_redshift

        total_hist, total_bins = mass_fn.total_mass_function(rck)
        plotter.total_mass_function(
            z, total_hist, total_bins, self._data.sim_name)

        # =================================================================
        # RHO BAR
        # =================================================================
        try:
            rb.rho_bar(rck)
        except Exception as e:
            logger.error(e)

        # Get the number of samples needed
        num_sphere_samples = self._conf.sampling.num_sp_samples

        # Iterate over the radii to sample for
        for radius in self._conf.radii:

            logger.debug(
                f"Calculating overdensities and halo mass functions at a radius of '{radius}'")  # noqa: E501

            # =================================================================
            # OVERDENSITIES:
            # =================================================================
            logger.info("Working on overdensities:")

            od = overdensity.Overdensity(self._data)
            deltas = od.calc_overdensities(rck, radius)

            # =================================================================
            # STANDARD DEVIATION
            # =================================================================
            logger.debug("Working on standard deviation")
            sd = standard_deviation.StandardDeviation(self._data)
            sd.std_dev(rck, radius)

            # =================================================================
            # MASS FUNCTION:
            # =================================================================
            logger.info("Working on mass function:")
            mf = mass_function.MassFunction(self._data)
            mass_hist, bin_edges = mf.mass_function(rck, radius)

            # Truncate the lists to the desired number of values
            # if there are too many
            deltas = deltas[:num_sphere_samples]

            logger.debug("Generating plots for this data...")

            plotter.overdensities(
                z,
                radius,
                deltas,
                self._data.sim_name,
                self._conf.sampling.num_od_hist_bins)
            plotter.mass_function(
                z, radius, mass_hist, bin_edges, self._data.sim_name)


def main(args):
    runner = MainRunner(args)
    runner.run()


if __name__ == "__main__":
    # Drop the program name from the sys.args
    main(sys.argv[1:])
