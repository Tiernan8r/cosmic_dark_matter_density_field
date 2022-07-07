import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from src import data
import yt
from src.const.constants import SPHERES_KEY
from src.init import setup
from src.util import coordinates, helpers


class Sampler(data.Data):

    def __init__(self, d: data.Data):
        super().__init__(*d.compile())

    def sample(self, rck, radius, z) -> list:

        key = (rck, SPHERES_KEY, z, float(radius))

        existing_samples = []
        if self._config.caches.use_sphere_samples:
            existing_samples = self._cache[key].val

        new_samples = self._cache_sample(rck, radius, existing_samples)

        self._cache[key] = new_samples

        return new_samples

    def _cache_sample(self, rck, radius, existing: list = None) -> list:
        """
        Randomly samples the data set with spheres of the given radius to find
        halos within that sample
        """
        logger = logging.getLogger(
            __name__ + "." + self._cache_sample.__name__)

        # Load the rockstar data set
        ds = self._dataset_cache.load(rck)

        # Get the distance units used by the simulation
        dist_units = ds.units.Mpc / ds.units.h
        # Convert the radius to the distance units
        R = (radius * dist_units).to("code_length")

        z = ds.current_redshift

        # Get the redshift from the cache
        a = 1 / (1+z)

        logger.debug(f"Redshift z={z}")

        # Get the size of the simulation
        sim_size = ds.domain_width[0]
        logger.debug(f"Simulation size = {sim_size}")

        # Bound the coordinate sampling, so that the spheres only overlap with
        # volumes within the simulation region
        coord_min = radius
        coord_max = sim_size.value - radius

        # Get the desired number of random coords for this sampling
        coords = coordinates.rand_coords(
            self._config.sampling.num_sp_samples, min=coord_min, max=coord_max) * dist_units

        # Truncate the number of values to calculate, if some already exist...
        masses = []
        if existing is not None:
            coords = coords[len(existing):]
            masses = existing
            logger.debug(
                f"Have {len(existing)} existing samples, need {self._config.sampling.num_sp_samples - len(existing)} more...")

        indexed_coords = [(i, coords[i]) for i in range(len(coords))]

        # Iterate over all the randomly sampled coordinates
        for ic in yt.parallel_objects(indexed_coords):
            i, c = ic[0], ic[1]

            logger.debug(
                f"({i}) Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")

            # Try to sample a sphere of the given radius at this coord
            try:
                sp = self._dataset_cache.sphere(rck, c, R)
            # Can error on higher redshift data sets due to sampling regions
            # erroring in yt
            except TypeError as te:
                logger.error("error creating sphere sample")
                logger.error(te)
                continue

            # Try to read the masses of halos in this sphere
            try:
                m = sp["halos", "particle_mass"]
            except TypeError as te:
                logger.error("error reading sphere halo masses")
                logger.error(te)
                continue

            logger.debug(f"Found {len(m)} halos in this sphere sample")

            # Add these masses to the list
            masses.append(m)

        logger.info(
            f"DONE reading {self._config.sampling.num_sp_samples} sphere samples\n")

        # Convert mass units to Msun
        # masses = masses.to(ds.units.Msun / ds.units.h)

        return masses


def main(args):
    if yt.is_root():

        # Setup logging/config reading & parallelisation
        d = setup.setup(args)

        logger = logging.getLogger(main.__name__)

        for sim_name in d.config.sim_data.simulation_names:
            d.sim_name = sim_name

            logger.info(f"Working on simulation: {sim_name}")

            # Find halos for data set
            logger.debug(
                f"Filtering halo files to look for redshifts: {d.config.redshifts}")
            _, _, rockstars = helpers.filter_data_files(
                d.sim_name, d.config.sim_data.root, d.config.redshifts)
            logger.debug(
                f"Found {len(rockstars)} rockstar files that match these redshifts")

            # Run the calculations over all the rockstar files found
            for rck in rockstars:

                sampler = Sampler(d)

                ds = d.dataset_cache.load(rck)
                z = ds.current_redshift
                logger.info(f"Redshift is: {z}")

                for radius in d.config.radii:
                    logger.info(f"Generating samples at r={radius} & z={z}")
                    sampler.sample(rck, radius, z)

                # Clear the data set cache between iterations as the
                # data isn't persistent anyway, and this saves memory
                logger.debug("Clearing dataset cache for new iteration")
                d.dataset_cache.clear()

            d.cache.reset()

            logger.info("DONE calculations\n")


if __name__ == "__main__":
    main(sys.argv[1:])
