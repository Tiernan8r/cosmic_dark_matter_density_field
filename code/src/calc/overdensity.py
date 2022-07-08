import logging

import numpy as np
import unyt
from src.calc import rho_bar
from src.const.constants import OVERDENSITIES_KEY


class Overdensity(rho_bar.RhoBar):

    def calc_overdensities(self, rck, radius):
        logger = logging.getLogger(
            __name__ + "." + self.calc_overdensities.__name__)

        logger.debug(
            f"Calculating cache values for '{OVERDENSITIES_KEY}'...")

        ds = self.dataset_cache.load(rck)
        z = ds.current_redshift

        # Get the number of samples needed
        num_sphere_samples = self.config.sampling.num_sp_samples

        # Attempt to get the existing overdensities if they exist
        key = (rck, OVERDENSITIES_KEY, z, float(radius))

        # Determine if new entries need to be calculates
        deltas = self.cache[key].val
        needs_recalculation = deltas is None

        # Calculation required if not enough entries cached
        if not needs_recalculation:
            amount_entries = len(deltas)
            logger.debug(
                f"Cache entries exist: Have {amount_entries}, need {num_sphere_samples}")
            needs_recalculation = amount_entries < num_sphere_samples
            logger.debug(f"Need more calculations: {needs_recalculation}")
        # Could force recalculation
        needs_recalculation |= not self.config.caches.use_overdensities_cache

        logger.debug(
            f"Override overdensities cache? {not self.config.caches.use_overdensities_cache}")

        # Calculate if required...
        if needs_recalculation:
            # Do the full sampling and save the cache to disk
            deltas = self._overdensities(rck, radius)
            # Cache the new values
            self.cache[key] = deltas
        else:
            logger.debug("Using cached overdensities...")

        return deltas

    def _overdensities(self, rck, radius):
        """
        Calculates the overdensities of a sample of spheres of a given radius over
        the given dataset, if there are existing samples, only calculates the extra
        samples required to get the total desired.
        """
        logger = logging.getLogger(
            __name__ + "." + self._overdensities.__name__)

        # Load the (cached?) data set
        ds = self._dataset_cache.load(rck)

        z = ds.current_redshift
        logger.debug(f"Redshift z={z}")

        sphere_samples = self.sample(rck, radius, z)

        # Get the units used in the simulation
        dist_units = ds.units.Mpc / ds.units.h
        # Convert the given radius to an unyt unit object
        R = radius * dist_units

        # Calculate the volume of the spheres that we sample on in comoving units
        V = 4/3 * np.pi * (R)**3

        # Get existing rhos
        rb = self.rho_bar(rck)

        deltas = []

        logger.info(f"Given rho_bar = {rb}")
        logger.info(f"Volume is: {V}")

        for sphere_sample in sphere_samples:
            total_mass = np.sum(sphere_sample)

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
