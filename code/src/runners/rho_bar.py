import logging
import os
import sys

# Required to guarantee that the 'src' module is accessible when
# this file is run directly.
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from src import runner
from src import units as u
from src.calc.rho_bar import RhoBar
from src.const.constants import RHO_BAR_0_KEY, RHO_BAR_KEY


class RhoBarRunner(runner.Runner):

    def tasks(self, hf: str):
        logger = logging.getLogger(
            __name__ + "." + RhoBarRunner.__name__ + "." + self.tasks.__name__)

        rb = RhoBar(self._data, type=self._type)

        if not self._conf.caches.use_rho_bar_cache:
            try:
                rb.rho_bar_0(hf)
                rb.rho_bar(hf)
            except TypeError as te:
                logger.warning(te)

            ds = self._ds_cache.load(hf)
            z = ds.current_redshift

            key_0 = (hf, RHO_BAR_0_KEY)
            key = (hf, self._type.value, RHO_BAR_KEY, z)

            rho_bar_0 = self._cache[key_0].val
            if rho_bar_0 is None:
                logger.warning("No rho_bar_0 found!")
            else:
                logger.info(f"Rho bar 0 is: {rho_bar_0}")
                logger.info(
                    f"Rho bar 0 in standard units is: {rho_bar_0.to(u.density(ds))}")

            rho_bar = self._cache[key].val
            if rho_bar is None:
                logger.warning("No rho bar found!")
            else:
                logger.info(f"Rho bar is: {rho_bar}")
                logger.info(
                    f"Rho bar in standard units is: {rho_bar.to(u.density(ds))}")

            logger.info("\n")


def main(args):
    rb_runner = RhoBarRunner(args)
    rb_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
