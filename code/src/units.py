

def mass(ds):
    return ds.mass_unit


def length(ds):
    return ds.units.Mpccm / ds.units.h


def density(ds):
    return mass(ds) / length(ds)**3
