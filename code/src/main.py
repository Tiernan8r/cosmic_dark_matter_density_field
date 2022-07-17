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

    def tasks(self, hf: str):
        logger = logging.getLogger(self.tasks.__name__)

        logger.debug(f"Working on halo file '{hf}'")

        logger.debug("Calculating total halo mass function")

        mf = mass_function.MassFunction(self._data, type=self._type)
        rb = rho_bar.RhoBar(self._data, type=self._type)
        od = overdensity.Overdensity(self._data, type=self._type)
        sd = standard_deviation.StandardDeviation(self._data, type=self._type)
        plotter = plotting.Plotter(self._data, self._type)

        # =================================================================
        # TOTAL MASS FUNCTION
        # =================================================================
        ds = self._ds_cache.load(hf)
        z = ds.current_redshift
        min_particle_mass = self._ds_cache.min_mass(hf)

        total_hist, total_bins = mf.total_mass_function(hf)
        plotter.total_mass_function(
            z, total_hist, total_bins, self._data.sim_name, min_particle_mass)

        # =================================================================
        # RHO BAR
        # =================================================================
        try:
            rb.rho_bar(hf)
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

            deltas = od.calc_overdensities(hf, radius)

            # =================================================================
            # STANDARD DEVIATION
            # =================================================================
            logger.debug("Working on standard deviation")
            sd.std_dev(hf, radius)

            # =================================================================
            # MASS FUNCTION:
            # =================================================================
            logger.info("Working on mass function:")
            mass_hist, bin_edges = mf.mass_function(hf, radius)

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
                z, radius, mass_hist, bin_edges, self._data.sim_name, min_particle_mass)


def main(args):
    runner = MainRunner(args)
    runner.run()


if __name__ == "__main__":
    # Drop the program name from the sys.args
    main(sys.argv[1:])
