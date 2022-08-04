from src.plotting import mass_function, overdensity, std_dev, fits


class Plotter(mass_function.MassFunction, overdensity.Overdensity, std_dev.StandardDeviation, fits.Fits):
    pass
