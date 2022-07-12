import datetime
import logging
import time

import unyt
import yt
from src import data
from src.const.constants import SPHERES_KEY
from src.util import coordinates


class Sampler(data.Data):

    def __init__(self, d: data.Data):
        super().__init__(*d.compile())

    def sample(self, rck, radius, z) -> list:

        logger = logging.getLogger(
            __name__ + "." + Sampler.__name__ + "." + self.sample.__name__)

        key = (rck, SPHERES_KEY, z, float(radius))
        num_sphere_samples = self._config.sampling.num_sp_samples
        samples = self._cache[key].val
        needs_recalculation = samples is None
        # run calculation if not enough values cached
        if not needs_recalculation:
            amount_entries = len(samples)
            logger.debug(
                f"Cache entries exist: Have {amount_entries}, need {num_sphere_samples}")  # noqa: E501
            needs_recalculation = amount_entries < num_sphere_samples
            logger.debug(f"Need more calculations: {needs_recalculation}")
        # Could force recalculation
        needs_recalculation |= not self._config.caches.use_sphere_samples
        logger.debug(
            f"Override spheres cache? {not self._config.caches.use_sphere_samples}")  # noqa: E501

        if needs_recalculation:
            samples = self._cache_sample(rck, radius, existing=samples)

            self._cache[key] = samples

        # Limit the sphere samples to be the number required if too many
        return samples[:num_sphere_samples]

    def _cache_sample(self, rck, radius, existing: list = None) -> list:
        """
        Randomly samples the data set with spheres of the given radius to find
        halos within that sample
        """
        logger = logging.getLogger(
            __name__ + "." + self._cache_sample.__name__)

        start = time.time()

        # Load the rockstar data set
        ds = self._dataset_cache.load(rck)

        # Get the distance units used by the simulation
        dist_units = ds.units.Mpc / ds.units.h
        # Convert the radius to the distance units
        R = (radius * dist_units).to("code_length")

        z = ds.current_redshift

        # Get the redshift from the cache
        # a = 1 / (1+z)

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
            self._config.sampling.num_sp_samples, min=coord_min, max=coord_max)
        coords = (coords * dist_units).to("code_length")

        # Truncate the number of values to calculate, if some already exist...
        sphere_samples = []
        if existing is not None:
            coords = coords[len(existing):]
            sphere_samples = existing
            logger.debug(
                f"Have {len(existing)} existing samples, need {self._config.sampling.num_sp_samples - len(existing)} more...")  # noqa: E501

        indexed_coords = [(i, coords[i]) for i in range(len(coords))]

        # Iterate over all the randomly sampled coordinates
        for ic in yt.parallel_objects(indexed_coords):
            i, c = ic[0], ic[1]

            logger.debug(
                f"({i}) Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")  # noqa: E501

            # Try to sample a sphere of the given radius at this coord
            try:
                sp = self._dataset_cache.sphere(rck, c, R)
            # Can error on higher redshift data sets due to sampling regions
            # erroring in yt
            except TypeError as te:
                logger.error("error creating sphere sample")
                logger.error(te)
                continue

            # TODO: unhard code?
            mass_units = ds.units.Msun / ds.units.h

            # Try to read the masses of halos in this sphere
            try:
                masses = sp["halos", "particle_mass"]
            except TypeError as te:
                logger.error("error reading sphere halo masses")
                logger.error(te)
                continue

            # filter for negative (!!!) masses
            filtered = unyt.unyt_array(
                [v for v in masses if v > 0], mass_units)

            logger.debug(f"Found {len(masses)} halos in this sphere sample")

            # Add these masses to the list
            sphere_samples.append(filtered)

        logger.info(
            f"DONE reading {self._config.sampling.num_sp_samples} sphere samples\n")  # noqa: E501

        # Convert mass units to Msun
        # masses = masses.to(ds.units.Msun / ds.units.h)

        end = time.time()
        logger.info(f"Took {datetime.timedelta(seconds=end - start)}")

        return sphere_samples
