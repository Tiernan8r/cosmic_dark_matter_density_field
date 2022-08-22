

def mass(ds):
    return ds.units.Msun / ds.units.h


def length_cm(ds):
    return ds.units.Mpccm / ds.units.h


def length(ds):
    return ds.units.Mpc / ds.units.h

def volume(ds):
    return ds.units.Mpc**3 * ds.units.h**-3

def volume_cm(ds):
    return ds.units.Mpccm**3 * ds.units.h**-3

def density_cm(ds):
    return mass(ds) / length_cm(ds)**3


def density(ds):
    return mass(ds) / length(ds)**3

def unit_base():
    return {
        "length": (1.0, "Mpccm/h")
    }