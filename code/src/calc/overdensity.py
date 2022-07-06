import logging

import numpy as np
import unyt
from src.calc.classes import sample


class Overdensity(sample.Sampler):

    def calc_overdensities(self, rck, radius, rho_bar, existing: unyt.unyt_array = None):
        """
        Calculates the overdensities of a sample of spheres of a given radius over
        the given dataset, if there are existing samples, only calculates the extra
        samples required to get the total desired.
        """
        logger = logging.getLogger(
            __name__ + "." + self.calc_overdensities.__name__)

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

        deltas = []

        for sphere_sample in sphere_samples:
            total_mass = np.sum(sphere_sample)
            # Get the density
            rho = total_mass / V
            # The overdensity
            delta = (rho - rho_bar) / rho_bar

            deltas.append(delta)

        # Return the units array of overdensities
        return unyt.unyt_array(deltas)
