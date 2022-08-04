from src.plotting.paths.interface import IPaths

class Fits(IPaths):

    def gaussian_fit_dir(self, sim_name):
        return self._compile_plot_dir(self.config.plotting.dirs.gaussian_fit,
                                      sim_name, self.type)

    def gaussian_fit_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self.config.plotting.dirs.gaussian_fit,
                                        self.config.plotting.pattern.gaussian_fit,  # noqa: E501
                                        sim_name, self.type, radius, z)

    def gaussian_title(self, sim_name, z):
        return f"Gaussian fit to overdensity for {sim_name} @ z={z:.2f}"

    def skewed_gaussian_fit_dir(self, sim_name):
        return self._compile_plot_dir(self.config.plotting.dirs.skewed_gaussian_fit,
                                      sim_name, self.type)

    def skewed_gaussian_fit_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self.config.plotting.dirs.skewed_gaussian_fit,
                                        self.config.plotting.pattern.skewed_gaussian_fit,  # noqa: E501
                                        sim_name, self.type, radius, z)

    def skewed_gaussian_title(self, sim_name, z):
        return f"Skewed Gaussian fit to overdensity for {sim_name} @ z={z:.2f}"

    def n_gaussian_fit_dir(self, sim_name):
        return self._compile_plot_dir(self.config.plotting.dirs.n_gaussian_fit,
                                      sim_name, self.type)

    def n_gaussian_fit_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self.config.plotting.dirs.n_gaussian_fit,
                                        self.config.plotting.pattern.n_gaussian_fit,  # noqa: E501
                                        sim_name, self.type, radius, z)

    def n_gaussian_title(self, sim_name, z):
        return f"N Gaussian fit to overdensity for {sim_name} @ z={z:.2f}"
