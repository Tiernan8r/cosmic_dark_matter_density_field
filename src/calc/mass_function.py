import logging
from typing import Tuple

import numpy as np
import src.calc.sample as sample
import unyt
import yt
from src.util import enum
from src.util import units as u
from src.util.constants import MASS_FUNCTION_KEY, TOTAL_MASS_FUNCTION_KEY


class MassFunction(sample.Sampler):

    def total_mass_function(self, hf) -> Tuple[np.ndarray, np.ndarray]:
        # Only need to run this once per file, so run only on root
        if not yt.is_root():
            return

        logger = logging.getLogger(
            __name__ + "." + self.total_mass_function.__name__)

        logger.debug("Calculating total mass function...")

        # Load in the halo data set, potentially from
        # a cache to optimise it
        ds = self.dataset_cache.load(hf)

        # Get the redshift from the data set
        z = ds.current_redshift

        # Cache the masses if they are not already

        # Get the cached values
        masses = self.cache_total_mass_function(hf)
        if masses is None:
            logger.debug("Skipping plotting this total mass function...")
            return None, None

        if len(masses) > 0:
            logger.info(f"Mass units are: {masses.units}")

        hist, bins = create_histogram(masses, self.config.sampling.num_hist_bins)

        # Calculate the scale factor
        a = 1 / (1+z)

        # Calculate the area of the box (is a cube)
        sim_size = ds.domain_width[0].to(u.length(ds))
        V = (a * sim_size)**3

        logger.info(f"Volume units are: {V.units}")

        # Divide the number of halos per bin by the
        # volume to get the number density
        hist = (hist / V).to(1 / u.volume(ds))

        return hist, bins

    def cache_total_mass_function(self, hf: str):
        """
        Runs the calculations of halo masses for the
        entire data set and caches the results
        """

        logger = logging.getLogger(
            __name__ + "." + self.cache_total_mass_function.__name__)

        logger.debug("Calculating total mass function...")

        # Load in the halo data set, potentially
        # from a cache to optimise it
        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        # If key is in cache, doesn't neet recalculation
        masses = self.cache[hf, self.type.value,
                            TOTAL_MASS_FUNCTION_KEY, z].val
        logger.debug(
            f"Override total mass cache? {not self.config.caches.use_total_cache}")  # noqa: E501

        # If a value for the calculation doesn't exist in the cache,
        # need to calculate it...
        if masses is None or not self.config.caches.use_total_cache:

            logger.debug(f"No masses cached for '{hf}' data set, caching...")

            # Try to read all the particle data from the data set
            # (can error with the earlierredshift data sets due
            # to box issues??)
            try:
                ad = self.dataset_cache.all_data(hf)
            except TypeError as te:
                logger.error("error reading all_data(), ignoring...")
                logger.error(te)
                return

            logger.info("Reading all halos in data set")
            # Get the halo virial masses from the data
            try:
                masses = ad[self.type.index]
            except yt.utilities.exceptions.YTFieldNotFound as ytfnf:
                logger.error(f"error reading masses from dataset!")
                logger.error(ytfnf)
                return

            if self.type is enum.DataType.ROCKSTAR:
                logger.info(
                    f"Filtering {len(masses)} entries for negative masses...")
                # Filter out negative masses (!!!)
                masses = masses[np.where(masses > 0)]

            # Cache the calculated values, and save the cache to disk
            self.cache[hf, self.type.value,
                       TOTAL_MASS_FUNCTION_KEY, z] = masses

        else:
            logger.debug("Using cached masses in plots...")

        return masses

    def mass_function(self, hf, radius):
        logger = logging.getLogger(
            __name__ + "." + self.mass_function.__name__)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        # Get the number of samples needed
        num_sphere_samples = self.config.sampling.num_sp_samples

        # If cache entries exist, may not need to recalculate
        key = (hf, self.type.value, MASS_FUNCTION_KEY, z, float(radius))
        masses = self.cache[key].val
        needs_recalculation = masses is None
        needs_recalculation |= not self.config.caches.use_masses_cache

        logger.debug(
            f"Override masses cache? {not self.config.caches.use_masses_cache}")  # noqa: E501

        # If the radius key is missing, need to do a full sample run
        if needs_recalculation:
            logger.debug(
                f"Calculating cache values for '{MASS_FUNCTION_KEY}'...")

            # Run the full sample, and save the result to the cache
            masses = self.sample_masses(hf, radius)
            self.cache[key] = masses

        # The key can exist, but there may not be enough samples...
        else:
            logger.debug("Using cached halo masses...")

        logger.info(f"Mass units are: {masses.units}")

        mass_hist, mass_bin_edges = create_histogram(masses, self.config.sampling.num_hist_bins)

        # Scale the histogram bins by the total volume sampled.
        a = 1 / (1+z)
        V = 4/3 * np.pi * (a*radius)**3 * num_sphere_samples

        mass_hist = mass_hist / V

        return mass_hist, mass_bin_edges

    def sample_masses(self, hf, radius):
        """
        Randomly samples the data set with spheres of the given radius to find
        halos within that sample
        """
        logger = logging.getLogger(
            __name__ + "." + self.sample_masses.__name__)

        # Load the halo data set
        ds = self.dataset_cache.load(hf)

        z = ds.current_redshift
        logger.debug(f"Redshift z={z}")

        sphere_samples = self.sample(hf, radius, z)

        # Convert the list of masses per sample, into a 1D list
        masses = ds.arr([], u.mass(ds))

        logger.info(f"Masses units are: {masses.units}")

        for m in sphere_samples:
            # Ensure the units match
            m = m.to(masses.units)
            masses = unyt.uconcatenate((masses, m))

        # Convert mass units to Msun
        masses = masses.to(u.mass(ds))

        return masses


def create_histogram(masses: unyt.unyt_array, bins) -> Tuple[
        np.ndarray,
        np.ndarray]:
    logger = logging.getLogger(__name__ + "." + create_histogram.__name__)

    logger.debug("Creating histogram")

    hist, bins = np.histogram(masses,
                              bins=bins)

    # Filter hist/bins for non-zero masses
    valid_idxs = np.where(hist > 0)
    hist = hist[valid_idxs]
    bins = bins[valid_idxs]

    return hist, bins