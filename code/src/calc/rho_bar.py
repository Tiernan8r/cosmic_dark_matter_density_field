#!/usr/bin/env python3
import logging

import src.calc.sample as sample
import unyt
from src import units as u
from src.const.constants import RHO_BAR_0_KEY, RHO_BAR_KEY, sim_regex
from src.util import halo_finder


class RhoBar(sample.Sampler):

    def rho_bar_0(self, hf):

        logger = logging.getLogger(__name__ + "." + self.rho_bar_0.__name__)

        sim_name = sim_regex.match(hf).group(1)

        logger.debug(
            f"Finding {self._type.value} file for a redshift of 0 on simulation '{sim_name}'")  # noqa: E501
        halos_finder = halo_finder.HalosFinder(
            halo_type=self.type, root=self.config.sim_data.root, sim_name=sim_name)
        halo_files = halos_finder.filter_data_files(desired=[0])

        if len(halo_files) > 1:
            logger.warning(
                "Too many halo files found for redshift 0, using last one!")  # noqa: E501
        hf = halo_files[-1]

        logger.info(f"Halo file is '{hf}'")

        ds = self.dataset_cache.load(hf)

        # =================================================================
        # CALCULATING RHO BAR 0
        # =================================================================
        logger.info("Working on rho bar 0 value:")

        rho_0 = self.cache[hf, self.type.value, RHO_BAR_0_KEY].val
        if rho_0 is None or not self.config.caches.use_rho_bar_cache:
            logger.debug(
                f"No entries found in cache for '{RHO_BAR_0_KEY}', calculating...")  # noqa: E501
            try:
                ad = self.dataset_cache.all_data(hf)
            except TypeError as te:
                logger.error("Error reading all_data()")
                logger.error(te)
                return

            simulation_total_mass = ad.quantities.total_mass()[
                1].to(u.mass(ds))
            logger.info(f"Simulation total mass is: {simulation_total_mass}")

            simulation_size = ds.domain_width[0].to(u.length(ds))
            logger.info(f"Simulation total size is: {simulation_size}")

            z = ds.current_redshift
            a = 1 / (1 + z)
            simulation_volume = (simulation_size * a) ** 3

            rho_0 = (simulation_total_mass /
                     simulation_volume).to(u.density(ds))

            self.cache[hf, self.type.value, RHO_BAR_0_KEY] = rho_0

        else:
            logger.debug("Using cached 'rho_bar_0' value...")

        logger.info(f"Rho bar 0 is: {rho_0}")

        return rho_0

    def rho_bar(self, hf):
        logger = logging.getLogger(__name__ + "." + self.rho_bar.__name__)

        # =================================================================
        # RHO BAR:
        # =================================================================
        logger.info("Working on rho_bar value:")

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        # Calculate the density of the entire region if is not cached...
        rho_bar = self.cache[hf, self.type.value, RHO_BAR_KEY, z].val
        if rho_bar is None or not self.config.caches.use_rho_bar_cache:
            logger.debug(
                f"No entries found in cache for '{RHO_BAR_KEY}', calculating...")  # noqa: E501

            # Try to calculate the rho_bar value
            try:
                rho_bar = self._calc_rho_bar(hf)
            # Can error on some of the earlier redshift data sets
            # due to region bounding issues
            # (don't know exactly why though...)
            except TypeError as te:
                logger.error("error getting all dataset region")
                logger.error(te)
                raise te
            # Can also error when the IGM is tagged as being
            # dimensionless rather than 0g...
            except unyt.exceptions.IterableUnitCoercionError as iuce:
                logger.error(
                    "Error reading regions quantities from database, ignoring...")  # noqa: E501
                logger.error(iuce)
                raise iuce

            # Cache the result
            self.cache[hf, self.type.value, RHO_BAR_KEY, z] = rho_bar

        else:
            logger.debug("Using cached 'rho_bar' value...")

        logger.info(f"Average density calculated as: {rho_bar}")
        logger.info(f"Density units are: {rho_bar.units}")

        return rho_bar

    def _calc_rho_bar(self, hf):
        """
        Calculates the overdensity of the entire data set
        """
        logger = logging.getLogger(
            __name__ + "." + self._calc_rho_bar.__name__)

        # Load the data set, if it is cached already this
        # operation will be faster...
        ds = self.dataset_cache.load(hf)

        # Get the distance units used in the code
        z = ds.current_redshift

        # Calculate the scale factor
        a = 1/(1+z)

        logger.debug(f"Redshift z={z}")

        # Get the size of one side of the box
        sim_size = (ds.domain_width[0]).to(u.length(ds))
        logger.debug(f"Simulation size = {sim_size}")
        logger.debug(f"Scale factor is: {a}")

        # Get the entire dataset region, can be cached for performance
        # optimisation
        ad = self.dataset_cache.all_data(hf)

        # Get the average density over the region
        total_mass = ad.quantities.total_mass()[1].to(u.mass(ds))
        volume = (sim_size * a)**3

        rho_bar = total_mass / volume

        logger.debug(
            f"Calculated a rho_bar of '{rho_bar}' for dataset '{hf}'")

        return rho_bar
