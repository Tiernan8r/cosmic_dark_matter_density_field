

def mass(ds):
    return ds.units.Msun / ds.units.h


def length_cm(ds):
    return ds.units.Mpccm / ds.units.h


def length(ds):
    return ds.units.Mpc / ds.units.h


def density_cm(ds):
    return mass(ds) / length_cm(ds)**3


def density(ds):
    return mass(ds) / length(ds)**3
