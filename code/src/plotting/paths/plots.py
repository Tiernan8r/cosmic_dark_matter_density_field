from src.plotting.paths.interface import IPaths


class Plots(IPaths):

    def mass_fn_dir(self, sim_name: str):
        return self._compile_plot_dir(self.config.plotting.dirs.mass_function,
                                      sim_name, self.type.value)

    def mass_fn_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self.config.plotting.dirs.mass_function,
                                        self.config.plotting.pattern.mass_function,  # noqa: E501
                                        sim_name, self.type.value, radius, z)

    def overdensity_dir(self, sim_name):
        return self._compile_plot_dir(self.config.plotting.dirs.overdensity,
                                      sim_name, self.type.value)

    def overdensity_fname(self, sim_name, radius, z):
        return self._compile_plot_fname(self.config.plotting.dirs.overdensity,
                                        self.config.plotting.pattern.overdensity,  # noqa: E501
                                        sim_name, self.type.value, radius, z)

    def total_dir(self, sim_name):
        return self._compile_plot_dir(self.config.plotting.dirs.total, sim_name, self.type.value)

    def total_fname(self, sim_name, z):
        return self._compile_plot_fname(self.config.plotting.dirs.total,
                                        self.config.plotting.pattern.total,
                                        sim_name, self.type.value, z)

    def press_schechter_dir(self, sim_name):
        return self._compile_plot_dir(self.config.plotting.dirs.press_schechter,
                                      sim_name, self.type.value)

    def press_schechter_fname(self, sim_name, z):
        return self._compile_plot_fname(self.config.plotting.dirs.press_schechter,  # noqa: E501
                                        self.config.plotting.pattern.press_schechter,  # noqa: E501
                                        sim_name, self.type.value, z)

    def numerical_mass_function_dir(self, sim_name, func_name):
        return self._compile_plot_dir(self.config.plotting.dirs.numerical_mass_function,
                                      sim_name, self.type.value, func_name)

    def numerical_mass_function_fname(self, sim_name, func_name, z):
        return self._compile_plot_fname(self.config.plotting.dirs.numerical_mass_function,  # noqa: E501
                                        self.config.plotting.pattern.numerical_mass_function,  # noqa: E501
                                        sim_name, self.type.value, func_name, z)

    def compared_dir(self, sim_name):
        return self._compile_plot_dir(self.config.plotting.dirs.compared,
                                      sim_name, self.type.value)

    def compared_fname(self, sim_name, z):
        return self._compile_plot_fname(self.config.plotting.dirs.compared,
                                        self.config.plotting.pattern.compared,
                                        sim_name, self.type.value, z)

    def std_dev_dir(self, sim_name):
        return self._compile_plot_dir(self.config.plotting.dirs.std_dev,
                                      sim_name, self.type.value)

    def std_dev_fname(self, sim_name, z):
        return self._compile_plot_fname(self.config.plotting.dirs.std_dev,
                                        self.config.plotting.pattern.std_dev,
                                        sim_name, self.type.value, z)
