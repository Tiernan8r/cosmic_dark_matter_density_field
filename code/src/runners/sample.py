import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from src import runner
from src.calc.sample import Sampler


class SampleRunner(runner.Runner):

    def rockstar_tasks(self, rck: str):
        logger = logging.getLogger(
            __name__ + "." + SampleRunner.__name__ + "." + self.rockstar_tasks.__name__)
        sampler = Sampler(self._data, type=self._type)

        ds = self._ds_cache.load(rck)
        z = ds.current_redshift

        logger.info(f"Redshift is: {z}")

        for radius in self._conf.radii:
            logger.info(f"Generating samples at r={radius} & z={z}")
            sampler.sample(rck, radius, z)


def main(args):
    sample_runner = SampleRunner(args)
    sample_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
