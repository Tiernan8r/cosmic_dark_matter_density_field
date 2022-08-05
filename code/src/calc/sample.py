import datetime
import logging
import time

import numpy as np
import yt
from src.util import enum, interface
from src.util import units as u
from src.util.constants import SAMPLES_KEY, SPHERES_KEY
from src.util.halos import coordinates


class Sampler(interface.Interface):

    def sample(self, hf, radius, z) -> list:

        logger = logging.getLogger(
            __name__ + "." + Sampler.__name__ + "." + self.sample.__name__)

        key = (hf, self.type.value, SPHERES_KEY, z, float(radius))
        num_sphere_samples = self.config.sampling.num_sp_samples
        samples = self.cache[key].val
        needs_recalculation = samples is None
        # run calculation if not enough values cached
        if not needs_recalculation:
            amount_entries = len(samples)
            logger.debug(
                f"Cache entries exist: Have {amount_entries}, need {num_sphere_samples}")  # noqa: E501
            needs_recalculation = amount_entries < num_sphere_samples
            logger.debug(f"Need more calculations: {needs_recalculation}")
        # Could force recalculation
        needs_recalculation |= not self.config.caches.use_sphere_samples
        logger.debug(
            f"Override spheres cache? {not self.config.caches.use_sphere_samples}")  # noqa: E501

        # Clear existing if overwriting
        if not self.config.caches.use_sphere_samples:
            samples = None

        if needs_recalculation:
            num_samples = len(samples) if samples is not None else 0

            # Calculate the sphere samples in batches to allow us to hotsave results for long calculations...
            max_num_samples_needed = self.config.sampling.num_sp_samples
            iteration_count = self.config.sampling.sphere_sample_iteration
            self.config.sampling.num_sp_samples = num_samples + iteration_count
            while num_samples < max_num_samples_needed:
                samples = self._cache_sample(hf, radius, existing=samples)
                self.config.sampling.num_sp_samples += iteration_count
                num_samples = len(samples)

                if self.config.sampling.sphere_sample_hotsave:
                    logger.info(
                        f"Hotsaving sphere samples at {num_samples} samples")
                    self.cache[key] = samples

            self.cache[key] = samples

        # Limit the sphere samples to be the number required if too many
        return samples[:num_sphere_samples]

    def _cache_sample(self, hf, radius, existing: list = None) -> list:
        """
        Randomly samples the data set with spheres of the given radius to find
        halos within that sample
        """
        logger = logging.getLogger(
            __name__ + "." + self._cache_sample.__name__)

        start = time.time()

        # Load the halo data set
        ds = self.dataset_cache.load(hf)

        # Get the distance units used by the simulation
        # Convert the radius to the distance units
        R = ds.quan(radius, u.length_cm(ds)).to("code_length")

        z = ds.current_redshift

        # Get the redshift from the cache
        # a = 1 / (1+z)

        logger.debug(f"Redshift z={z}")

        # Get the size of the simulation
        sim_size = ds.domain_width[0]
        logger.debug(f"Simulation size = {sim_size}")

        # Bound the coordinate sampling, so that the spheres only overlap with
        # volumes within the simulation region
        max_radius = self.config.max_radius
        coord_min = max_radius
        coord_max = sim_size.value - max_radius

        # Get the desired number of random coords for this sampling
        coords = coordinates.rand_coords(
            self.config.sampling.num_sp_samples, min=coord_min, max=coord_max)
        coords = ds.arr(coords, u.length_cm(ds)).to("code_length")

        # Truncate the number of values to calculate, if some already exist...
        sphere_samples = []
        if existing is not None:
            coords = coords[len(existing):]
            sphere_samples = existing

            num_sp_samples = self.config.sampling.num_sp_samples
            num_samples_needed = min(
                num_sp_samples - len(existing), num_sp_samples)
            logger.debug(
                f"Have {len(existing)} existing samples, need {num_samples_needed} more...")  # noqa: E501

        num_coords = len(coords)
        indexed_coords = [(i, coords[i]) for i in range(num_coords)]
        num_errors = 0

        # Iterate over all the randomly sampled coordinates
        for ic in yt.parallel_objects(indexed_coords):
            it_start = time.time()

            i, c = ic[0], ic[1]

            logger.debug(
                f"({i}) Creating sphere @ ({c[0]}, {c[1]}, {c[2]}) with radius {R}")  # noqa: E501

            # Try to sample a sphere of the given radius at this coord
            try:
                sp = self.dataset_cache.sphere(hf, c, R)
            # Can error on higher redshift data sets due to sampling regions
            # erroring in yt
            except TypeError as te:
                logger.error("error creating sphere sample")
                logger.error(te)
                num_errors += 1
                continue

            # Try to read the masses of halos in this sphere
            try:
                masses = sp[self.type.index]
            except TypeError as te:
                logger.error("error reading sphere halo masses")
                logger.error(te)
                num_errors += 1
                continue
            except yt.utilities.exceptions.YTFieldNotFound as ytfnf:
                logger.error("Could not access masses field")
                logger.error(ytfnf)
                num_errors += 1
                continue

            if self.type is enum.DataType.ROCKSTAR:
                # filter for negative (!!!) masses
                masses = masses[np.where(masses > 0)]

            logger.debug(f"Found {len(masses)} halos in this sphere sample")

            it_end = time.time()
            logger.debug(
                f"Took {datetime.timedelta(seconds=it_end - it_start)}")

            # Add these masses to the list
            sphere_samples.append(masses)

        # If all sampling errored, return an exception...
        if num_errors == num_coords:
            raise ValueError("Couldn't get any non erroring samples!")

        logger.info(
            f"DONE reading {self.config.sampling.num_sp_samples} sphere samples\n")  # noqa: E501

        end = time.time()
        logger.info(f"Took {datetime.timedelta(seconds=end - start)}")

        return sphere_samples

    def save_num_samples(self, hf: str, radius: float, z: float, num: int):
        key = (hf, self.type.value, SPHERES_KEY, z, float(radius), SAMPLES_KEY)
        self.cache[key] = num

    def get_num_samples(self, hf: str, radius: float, z: float) -> int:
        key = (hf, self.type.value, SPHERES_KEY, z, float(radius), SAMPLES_KEY)
        return self.cache[key].val
