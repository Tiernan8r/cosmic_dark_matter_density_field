import logging

import numpy as np
import unyt
import yt
from src.calc.classes import sample
from src.const.constants import MASS_FN_PLOTS_DIR, TOTAL_MASS_FUNCTION_KEY
from src.plot import plotting


class MassFunction(sample.Sampler):

    def total_mass_function(self, rck):
        # Only need to run this once per file, so run only on root
        if not yt.is_root():
            return

        logger = logging.getLogger(
            __name__ + "." + self.total_mass_function.__name__)

        logger.debug("Calculating total mass function...")

        # Load in the rockstar data set, potentially from a cache to optimise it
        ds = self._dataset_cache.load(rck)

        # Get the redshift from the data set
        z = ds.current_redshift

        # Cache the masses if they are not already

        # Get the cached values, the _cache_total_mass_function() method can error,
        # so need to use the get() notation
        masses = self.cache_total_mass_function(rck)
        if masses is None:
            logger.debug("Skipping plotting this total mass function...")
            return

        if len(masses) > 0:
            logger.info(f"Mass units are: {masses.units}")

        bin_min = np.log10(np.min(masses))
        bin_max = np.log10(np.max(masses))
        log_bins = np.logspace(bin_min, bin_max, self._config.num_hist_bins)

        # Calculate the histogram of the masses
        hist, bins = np.histogram(masses, bins=log_bins)

        # Filter hist/bins for non-zero masses
        valid_idxs = np.where(hist > 0)
        hist = hist[valid_idxs]
        bins = bins[valid_idxs]

        # Calculate the scale factor
        a = 1 / (1+z)

        # Calculate the area of the box (is a cube)
        sim_size = ds.domain_width[0].to(ds.units.Mpc / ds.units.h)
        V = (a * sim_size)**3

        logger.info(f"Volume units are: {V.units}")

        # Divide the number of halos per bin by the volume to get the number density
        hist = hist / V

        # Set the parameters used for the plotting & plot the mass function
        title = f"Total Mass Function for z={z:.2f}"
        save_dir = MASS_FN_PLOTS_DIR.format(self._sim_name)
        plot_name = (MASS_FN_PLOTS_DIR +
                     "total_mass_function_z{1:.2f}.png").format(self._sim_name, z)

        plotting.plot_mass_function(hist, bins, title, save_dir, plot_name)

    def cache_total_mass_function(self, rck: str):
        """
        Runs the calculations of halo masses for the entire data set and caches the results
        """

        logger = logging.getLogger(
            __name__ + "." + self.cache_total_mass_function.__name__)

        logger.debug("Calculating total mass function...")

        # Load in the rockstar data set, potentially from a cache to optimise it
        ds = self._dataset_cache.load(rck)
        z = ds.current_redshift

        # If key is in cache, doesn't neet recalculation
        masses = self._cache[rck, TOTAL_MASS_FUNCTION_KEY, z].val
        logger.debug(
            f"Override total mass cache? {not self._config.use_total_masses_cache}")

        # If a value for the calculation doesn't exist in the cache, need to calculate it...
        if masses is None or not self._config.use_total_masses_cache:

            logger.debug(f"No masses cached for '{rck}' data set, caching...")

            # Try to read all the particle data from the data set (can error with the earlier
            # redshift data sets due to box issues??)
            try:
                ad = self._dataset_cache.all_data(rck)
            except TypeError as te:
                logger.error("error reading all_data(), ignoring...")
                logger.error(te)
                return

            # Get the halo virial masses from the data
            masses = ad["halos", "particle_mass"]

            # Also store the redshift of this data set if it isn't cached already
            z = ds.current_redshift

            # Cache the calculated values, and save the cache to disk
            self._cache[rck, TOTAL_MASS_FUNCTION_KEY, z] = masses

        else:
            logger.debug("Using cached masses in plots...")

        return masses

    def sample_masses(self, rck, radius, existing: unyt.unyt_array = None):
        """
        Randomly samples the data set with spheres of the given radius to find
        halos within that sample
        """
        logger = logging.getLogger(
            __name__ + "." + self.sample_masses.__name__)

        # Load the rockstar data set
        ds = self._dataset_cache.load(rck)

        z = ds.current_redshift
        logger.debug(f"Redshift z={z}")

        sphere_samples = self.sample(rck, radius, z)

        # Convert the list of masses per sample, into a 1D list
        masses = unyt.unyt_array([], ds.units.Msun / ds.units.h)

        for m in sphere_samples:
            masses = unyt.uconcatenate((masses, m))

        # Convert mass units to Msun
        masses = masses.to(ds.units.Msun / ds.units.h)

        return masses
