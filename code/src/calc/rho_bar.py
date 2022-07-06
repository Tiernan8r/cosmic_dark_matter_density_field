#!/usr/bin/env python3
import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import unyt
from src.cache import caching
from src.calc.classes import calculator
from src.const.constants import RHO_BAR_0_KEY, RHO_BAR_KEY, sim_regex
from src.init import setup
from src.util import helpers


class RhoBar(calculator.Calculator):

    def rho_bar_0(self, rck):

        logger = logging.getLogger(__name__ + "." + self.rho_bar_0.__name__)

        sim_name = sim_regex.match(rck).group(1)

        logger.debug(
            f"Finding rockstar file for a redshift of 0 on simulation '{sim_name}'")
        _, _, rockstars = helpers.filter_data_files(sim_name, desired=[0])

        if len(rockstars) > 1:
            logger.warning(
                "Too many rockstar files found for redshift 0, using last one!")
        rck = rockstars[-1]

        logger.info(f"Rockstar file is '{rck}'")

        ds = self._dataset_cache.load(rck)

        # mass_units = ds.units.Msun / ds.units.h
        # dist_units = ds.units.Mpc / ds.units.h
        # density_units = mass_units / dist_units**3

        # =================================================================
        # CALCULATING RHO BAR 0
        # =================================================================
        logger.info(f"Working on rho bar 0 value:")

        rho_0 = self._cache[rck, RHO_BAR_0_KEY].val
        if rho_0 is None or not self._config.use_rho_bar_cache:
            logger.debug(
                f"No entries found in cache for '{RHO_BAR_0_KEY}', calculating...")
            try:
                ad = self._dataset_cache.all_data(rck)
            except TypeError as te:
                logger.error("Error reading all_data()")
                logger.error(te)
                return

            # simulation_total_mass = ad.quantities.total_mass()[
            #     1].to(mass_units)
            simulation_total_mass = ad.quantities.total_mass()[
                1]
            logger.info(f"Simulation total mass is: {simulation_total_mass}")

            # simulation_size = ds.domain_width[0].to(dist_units)
            simulation_size = ds.domain_width[0]
            logger.info(f"Simulation total size is: {simulation_size}")

            simulation_volume = simulation_size ** 3

            # rho_0 = (simulation_total_mass /
            #          simulation_volume).to(density_units)
            rho_0 = (simulation_total_mass /
                     simulation_volume)

            self._cache[rck, RHO_BAR_0_KEY] = rho_0

        else:
            logger.debug("Using cached 'rho_bar_0' value...")

        logger.info(f"Rho bar 0 is: {rho_0}")

        return rho_0

    def rho_bar(self, rck):
        logger = logging.getLogger(__name__ + "." + self.rho_bar.__name__)

        # =================================================================
        # RHO BAR:
        # =================================================================
        logger.info("Working on rho_bar value:")

        ds = self._dataset_cache.load(rck)
        z = ds.current_redshift

        # Calculate the density of the entire region if is not cached...
        rho_bar = self._cache[rck, RHO_BAR_KEY, z].val
        if rho_bar is None or not self._config.use_rho_bar_cache:
            logger.debug(
                f"No entries found in cache for '{RHO_BAR_KEY}', calculating...")

            # Try to calculate the rho_bar value
            try:
                rho_bar = self._calc_rho_bar(rck)
            # Can error on some of the earlier redshift data sets due to region bounding issues
            # (don't know exactly why though...)
            except TypeError as te:
                logger.error("error getting all dataset region")
                logger.error(te)
                raise te
            # Can also error when the IGM is tagged as being dimensionless rather than 0g...
            except unyt.exceptions.IterableUnitCoercionError as iuce:
                logger.error(
                    "Error reading regions quantities from database, ignoring...")
                logger.error(iuce)
                raise iuce

            # Cache the result
            self._cache[rck, RHO_BAR_KEY, z] = rho_bar

        else:
            logger.debug("Using cached 'rho_bar' value...")

        logger.info(f"Average density calculated as: {rho_bar}")
        logger.info(f"Density units are: {rho_bar.units}")

    def _calc_rho_bar(self, rck):
        """
        Calculates the overdensity of the entire data set
        """
        logger = logging.getLogger(
            __name__ + "." + self._calc_rho_bar.__name__)

        # Load the data set, if it is cached already this operation will be faster...
        ds = self._dataset_cache.load(rck)

        # Get the distance units used in the code
        # dist_units = ds.units.Mpc / ds.units.h

        z = ds.current_redshift

        # Calculate the scale factor
        a = 1/(1+z)

        logger.debug(f"Redshift z={z}")

        # Get the size of one side of the box
        # sim_size = (ds.domain_width[0]).to(dist_units)
        sim_size = (ds.domain_width[0])
        logger.debug(f"Simulation size = {sim_size}")

        # Get the entire dataset region, can be cached for performance
        # optimisation
        ad = self._dataset_cache.all_data(rck)

        # Get the average density over the region
        total_mass = ad.quantities.total_mass()[1]
        volume = (sim_size * a)**3

        rho_bar = total_mass / volume

        logger.debug(
            f"Calculated a rho_bar of '{rho_bar}' for dataset '{rck}'")

        return rho_bar


def main(args):
    conf, ds_cache = setup.setup(args)

    logger = logging.getLogger(main.__name__)

    sim_names = conf.sim_names
    for sim_name in sim_names:
        logger.debug(f"Showing average densities for '{sim_name}'")

        cache = caching.Cache()

        rb = RhoBar(conf, ds_cache, cache, sim_name)
        _, _, rockstars = helpers.filter_data_files(sim_name, conf.redshifts)
        for rck in rockstars:

            if not conf.use_rho_bar_cache:
                try:
                    rb.rho_bar_0(rck)
                    rb.rho_bar(rck)
                except TypeError as te:
                    logger.warning(te)

            ds = ds_cache.load(rck)
            z = ds.current_redshift

            key_0 = (rck, RHO_BAR_0_KEY)
            key = (rck, RHO_BAR_KEY, z)

            mass_units = ds.units.Msun / ds.units.h
            dist_units = ds.units.Mpc / ds.units.h
            standard_units = mass_units / dist_units**3

            rho_bar_0 = cache[key_0].val
            if rho_bar_0 is None:
                logger.warning(f"No rho_bar_0 found!")
            else:
                logger.info(f"Rho bar 0 is: {rho_bar_0}")
                logger.info(
                    f"Rho bar 0 is: {rho_bar_0.to(standard_units)}")

            rho_bar = cache[key].val
            if rho_bar is None:
                logger.warning(f"No rho bar found!")
            else:
                logger.info(f"Rho bar is: {rho_bar}")
                logger.info(
                    f"Rho bar is: {rho_bar.to(standard_units)}")

            logger.info("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
