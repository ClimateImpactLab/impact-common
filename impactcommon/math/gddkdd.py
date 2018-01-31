import numpy as np
import warnings

warnings.simplefilter("ignore", RuntimeWarning)

def above_threshold(mins, maxs, threshold):
    """Use a sinusoidal approximation to estimate the number of Growing
Degree-Days above a given threshold, using daily minimum and maximum
temperatures.

mins and maxs are numpy arrays; threshold is in the same units."""

    # Determine crossing points, as a fraction of the day
    plus_over_2 = (mins + maxs)/2
    minus_over_2 = (maxs - mins)/2
    two_pi = 2*np.pi
    # d0s is the times of crossing above; d1s is when cross below
    d0s = np.arcsin((threshold - plus_over_2) / minus_over_2) / two_pi
    d1s = .5 - d0s

    # If always above or below threshold, set crossings accordingly
    aboves = mins >= threshold
    belows = maxs <= threshold

    d0s[aboves] = 0
    d1s[aboves] = 1
    d0s[belows] = 0
    d1s[belows] = 0

    # Calculate integral
    F1s = -minus_over_2 * np.cos(2*np.pi*d1s) / two_pi + plus_over_2 * d1s
    F0s = -minus_over_2 * np.cos(2*np.pi*d0s) / two_pi + plus_over_2 * d0s
    return np.sum(F1s - F0s - threshold * (d1s - d0s))

def get_gddkdd(mins, maxs, gdd_start, kdd_start):
    """Get the Growing Degree-Days, as degree-days between gdd_start and
kdd_start, and Killing Degree-Days, as the degree-days above
kdd_start.

mins and maxs are numpy arrays; threshold is in the same units."""

    dd_lowup = above_threshold(mins, maxs, gdd_start)
    dd_above = above_threshold(mins, maxs, kdd_start)
    dd_lower = dd_lowup - dd_above

    return (dd_lower, dd_above)
