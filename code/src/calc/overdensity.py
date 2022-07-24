import logging
import math

import numpy as np
import unyt
from src import units as u
from src.calc import rho_bar
from src.const.constants import OVERDENSITIES_KEY


class Overdensity(rho_bar.RhoBar):

    def calc_overdensities(self, hf, radius):
        logger = logging.getLogger(
            __name__ + "." + self.calc_overdensities.__name__)

        logger.debug(
            f"Calculating cache values for '{OVERDENSITIES_KEY}'...")

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        # Get the number of samples needed
        num_sphere_samples = self.config.sampling.num_sp_samples

        # Attempt to get the existing overdensities if they exist
        key = (hf, self.type.value, OVERDENSITIES_KEY, z, float(radius))

        # Determine if new entries need to be calculates
        deltas = self.cache[key].val
        needs_recalculation = deltas is None

        # Calculation required if not enough entries cached
        if not needs_recalculation:
            amount_entries = len(deltas)
            logger.debug(
                f"Cache entries exist: Have {amount_entries}, need {num_sphere_samples}")  # noqa: E501
            needs_recalculation = amount_entries < num_sphere_samples
            logger.debug(f"Need more calculations: {needs_recalculation}")
        # Could force recalculation
        needs_recalculation |= not self.config.caches.use_overdensities_cache

        logger.debug(
            f"Override overdensities cache? {not self.config.caches.use_overdensities_cache}")  # noqa: E501

        # Calculate if required...
        if needs_recalculation:
            # Do the full sampling and save the cache to disk

            # Increase the sampling size per iteration until the std dev
            # converges
            prev_std_dev, std_dev = 0, -1
            upper_lim_num_sp_samples = self._config.sampling.num_sp_samples

            self._config.sampling.num_sp_samples = self._config.sampling.sample_iteration
            logger.info(
                f"Initial num sp samples = {self._config.sampling.num_sp_samples}")
            while not math.isclose(std_dev, prev_std_dev, abs_tol=self.config.sampling.overdensity_std_dev_tol) \
                    or self._config.sampling.num_sp_samples <= upper_lim_num_sp_samples:
                prev_std_dev = std_dev
                deltas = self._overdensities(hf, radius)
                std_dev = np.std(deltas)
                logger.debug(f"Old Std dev: {prev_std_dev}")
                logger.debug(f"New std dev: {std_dev}")
                self._config.sampling.num_sp_samples += self._config.sampling.sample_iteration
                logger.debug(
                    f"Increasing num sphere samples to: {self._config.sampling.num_sp_samples}")

            logger.info(
                f"Took {self._config.sampling.num_sp_samples} sphere samples to converge!")

            # Cache the new values
            self.cache[key] = deltas
            # Keep a record of the number of samples used...
            self.save_num_samples(
                hf, radius, z, self._config.sampling.num_sp_samples)
        else:
            logger.debug("Using cached overdensities...")

        return deltas

    def _overdensities(self, hf, radius):
        """
        Calculates the overdensities of a sample of spheres
        of a given radius over the given dataset, if there
        are existing samples, only calculates the extra
        samples required to get the total desired.
        """
        logger = logging.getLogger(
            __name__ + "." + self._overdensities.__name__)

        # Load the (cached?) data set
        ds = self.dataset_cache.load(hf)

        z = ds.current_redshift
        logger.debug(f"Redshift z={z}")

        sphere_samples = self.sample(hf, radius, z)

        # Get the units used in the simulation
        # Convert the given radius to an unyt unit object
        R = ds.quan(radius, u.length_cm(ds))

        # Calculate the volume of the spheres that we sample
        # on in comoving units
        V = 4/3 * np.pi * R**3

        # Get existing rhos
        rb = self.rho_bar(hf)

        deltas = []

        logger.info(f"Given rho_bar = {rb}")
        logger.info(f"Volume of sphere is: {V}")

        total_mass = ds.quan(0, u.mass(ds))
        rho = unyt.unyt_quantity(0)

        for sphere_sample in sphere_samples:
            total_mass = np.sum(sphere_sample)
            total_mass = total_mass.to(u.mass(ds))

            # Get the density
            rho = total_mass / V

            # Ensure the density units match to get a dimensionless quantity
            rho = rho.to(rb.units)

            # The overdensity
            delta = (rho - rb) / rb

            deltas.append(delta)

        logger.info(f"Total mass units are: {total_mass.units}")
        logger.info(f"Rho units are: {rho.units}")

        # Return the units array of overdensities
        unyt_deltas = unyt.unyt_array(deltas)

        logger.info(f"Deltas units are: {unyt_deltas.units}")

        return unyt_deltas
