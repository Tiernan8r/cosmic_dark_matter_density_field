import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import yt
from src.util import orchestrator
from src.calc.sample import Sampler


class SampleRunner(orchestrator.Orchestrator):

    def tasks(self, hf: str):
        logger = logging.getLogger(
            __name__ + "." + SampleRunner.__name__ + "." + self.tasks.__name__)
        sampler = Sampler(self, self.type, self.sim_name)

        ds = self.dataset_cache.load(hf)
        z = ds.current_redshift

        logger.info(f"Redshift is: {z}")

        radii = self.config.radii
        for radius in yt.parallel_objects(radii):
            logger.info(f"Generating samples at r={radius} & z={z}")
            sampler.sample(hf, radius, z)


def main(args):
    sample_runner = SampleRunner(args)
    sample_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
