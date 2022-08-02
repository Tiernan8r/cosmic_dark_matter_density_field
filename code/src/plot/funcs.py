import numpy as np
import scipy.special as sp


# Define model function to be used to fit to the data above:
def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))


# From: https://stackoverflow.com/a/48052931
def _skew(x, sigmag, mu, alpha, c, a):
    normpdf = (1 / (sigmag * np.sqrt(2 * np.pi))) * \
        np.exp(-(np.power((x - mu), 2) / (2 * np.power(sigmag, 2))))
    normcdf = (0.5 * (1 + sp.erf((alpha * ((x - mu) / sigmag)) / (np.sqrt(2)))))
    return 2 * a * normpdf * normcdf + c, max(normpdf)


def skew(x, sigmag, mu, alpha, c, a):
    return _skew(x, sigmag, mu, alpha, c, a)[0]

# From: https://stackoverflow.com/a/26954881


def n_gaussian(x, *params):
    y = np.zeros_like(x)

    for i in range(0, len(params), 3):
        ctr = params[i]
        amp = params[i+1]
        wid = params[i+2]
        y = y + amp * np.exp(-((x - ctr)/wid)**2)

    return y
