import logging
import sys

from src import runner
from src.calc.rho_bar import RhoBar
from src.const.constants import RHO_BAR_0_KEY, RHO_BAR_KEY


class RhoBarRunner(runner.Runner):

    def tasks(self, rck: str):
        logger = logging.getLogger(
            __name__ + "." + RhoBarRunner.__name__ + "." + self.tasks.__name__)

        rb = RhoBar(self._data)

        if not self._conf.caches.use_rho_bar_cache:
            try:
                rb.rho_bar_0(rck)
                rb.rho_bar(rck)
            except TypeError as te:
                logger.warning(te)

            ds = self._ds_cache.load(rck)
            z = ds.current_redshift

            key_0 = (rck, RHO_BAR_0_KEY)
            key = (rck, RHO_BAR_KEY, z)

            mass_units = ds.units.Msun / ds.units.h
            dist_units = ds.units.Mpc / ds.units.h
            standard_units = mass_units / dist_units**3

            rho_bar_0 = self._cache[key_0].val
            if rho_bar_0 is None:
                logger.warning(f"No rho_bar_0 found!")
            else:
                logger.info(f"Rho bar 0 is: {rho_bar_0}")
                logger.info(
                    f"Rho bar 0 is: {rho_bar_0.to(standard_units)}")

            rho_bar = self._cache[key].val
            if rho_bar is None:
                logger.warning(f"No rho bar found!")
            else:
                logger.info(f"Rho bar is: {rho_bar}")
                logger.info(
                    f"Rho bar is: {rho_bar.to(standard_units)}")

            logger.info("\n")


def main(args):
    rb_runner = RhoBarRunner(args)
    rb_runner.run()


if __name__ == "__main__":
    main(sys.argv[1:])
