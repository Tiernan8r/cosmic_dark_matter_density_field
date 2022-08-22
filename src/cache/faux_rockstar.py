from __future__ import annotations

import logging
import os
from typing import Any

import astropy.table.table
import unyt
import yt
import yt.data_objects.selection_objects.data_selection_objects
import yt.data_objects.selection_objects.region
import yt.frontends.rockstar.data_structures
from astropy.io import ascii

ATTRIBUTES_MAP = {
    ("halos", "particle_mass"): "mvir"
}


class FauxRockstar:

    def __init__(self, ds: yt.frontends.rockstar.data_structures.RockstarDataset, filename: str):
        self._fname = filename
        self._ds = ds

        logger = logging.getLogger(
            __name__ + "." + FauxRockstar.__name__ + "." + self.__init__.__name__)

        logger.debug("Initialising rockstar dataset wrapper")

        dirpath = os.path.dirname(filename)
        basename = os.path.basename(filename)

        fname, ext = os.path.splitext(basename)

        ascii_fname = fname + ".ascii"
        ascii_dirpath = os.path.join(dirpath, ascii_fname)

        logger.debug(f"Associated ascii file is at: {ascii_dirpath}")

        self._ascii_data = ascii.read(
            ascii_dirpath, format="fast_commented_header")

        logger.debug("Read in ascii data...")

    def all_data(self, find_max=False, **kwargs):
        ad = self._ds.all_data(find_max, **kwargs)

        return FauxSelection(ad, self._ascii_data)

    def sphere(self, centre, radius: float):
        sp = self._ds.sphere(centre, radius)

        return FauxSelection(sp, self._ascii_data)

    @property
    def current_redshift(self):
        return self._ds.current_redshift

    @property
    def domain_width(self):
        return self._ds.domain_width

    @property
    def parameters(self):
        return self._ds.parameters

    @property
    def units(self):
        return self._ds.units

    def arr(self, *args, **kwargs):
        return self._ds.arr(*args, **kwargs)

    def quan(self, *args, **kwargs):
        return self._ds.quan(*args, **kwargs)


class FauxSelection(yt.data_objects.selection_objects.data_selection_objects.YTSelectionContainer3D):

    def __init__(self, data: yt.data_objects.selection_objects.data_selection_objects.YTSelectionContainer3D, overrides: astropy.table.table.Table = None):
        self._data = data
        self._overrides = overrides

    def __getattribute__(self, __name: str) -> Any:

        attr = self._data[__name]

        if __name in ATTRIBUTES_MAP:
            conv = ATTRIBUTES_MAP[__name]
            val = self._overrides.get(conv, attr)
            attr = unyt.unyt_array(val, attr.units)

        return attr
