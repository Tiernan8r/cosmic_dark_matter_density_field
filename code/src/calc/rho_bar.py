#!/usr/bin/env python3
import functools
import logging
from src.util.halos import halo_finder

from src.calc import sample
from src.util.constants import RHO_BAR_0_KEY, RHO_BAR_KEY, sim_regex
from src.util.halos import snapshot_matcher
from src.util import units as u


class RhoBar(sample.Sampler):

    @functools.lru_cache(maxsize=1)
    def rho_bar_0(self):

        logger = logging.getLogger(__name__ + "." + self.rho_bar_0.__name__)

        logger.debug(
            f"Finding {self.type.value} file for a redshift of 0 on simulation '{self.sim_name}'")  # noqa: E501
        halos_finder = halo_finder.HalosFinder(
            halo_type=self.type, root=self.config.sim_data.root, sim_name=self.sim_name)
        halo_files = halos_finder.filter_data_files(desired=[0])
        hf0 = halo_files[0]

        # =================================================================
        # CALCULATING RHO BAR 0
        # =================================================================
        logger.info("Working on rho bar 0 value:")

        logger.debug(f"Matching snapshot simulation file")
        shf = snapshot_matcher.match_snapshot(
            self.config, self.dataset_cache, hf0)

        ds = self.dataset_cache.load(shf)
        ds_h = self.dataset_cache.load(hf0)

        rho_0 = self.cache[shf, RHO_BAR_0_KEY].val
        if rho_0 is None or not self.config.caches.use_rho_bar_0_cache:
            logger.debug(
                f"No entries found in cache for '{RHO_BAR_0_KEY}', calculating...")  # noqa: E501
            try:
                ad = self.dataset_cache.all_data(shf)
            except TypeError as te:
                logger.error("Error reading all_data()")
                logger.error(te)
                return

            all_masses = ad.quantities.total_mass()

            dust_mass = all_masses[0].to(u.mass(ds_h))
            clumps_mass = all_masses[1].to(u.mass(ds_h))

            total_mass = dust_mass + clumps_mass

            logger.info(f"Simulation total mass is: {total_mass}")

            simulation_size = ds.domain_width[0].to(u.length(ds_h))
            logger.info(f"Simulation total size is: {simulation_size}")

            simulation_volume = (simulation_size) ** 3

            rho_0 = (total_mass /
                     simulation_volume).to(u.density(ds))

            self.cache[shf, RHO_BAR_0_KEY] = rho_0

        else:
            logger.debug("Using cached 'rho_bar_0' value...")

        logger.info(f"Rho bar 0 is: {rho_0}")

        return rho_0

    @functools.lru_cache(maxsize=1)
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

            rb0 = self.rho_bar_0(hf)
            rho_bar = rb0 * (1 + z)**3
            rho_bar = rho_bar.to(u.density(ds))
            logger.debug(
                f"Calculated a rho_bar of '{rho_bar}' for dataset '{hf}'")

            # Cache the result
            self.cache[hf, self.type.value, RHO_BAR_KEY, z] = rho_bar

        else:
            logger.debug("Using cached 'rho_bar' value...")

        logger.info(f"Average density calculated as: {rho_bar}")
        logger.info(f"Density units are: {rho_bar.units}")

        return rho_bar
