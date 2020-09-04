######
# These functions calculate the minima and maxima of a cubic spline.
# The main function is `findsplinemin` and `findsplinemax`.
######

## Find extremum of expression of the form intercept x + sum(coeffs[i] (x - offsets[i])^3)
import numpy as np
from openest.models.curve import CubicSplineCurve

def quadratic(aa, bb, cc):
    if bb**2 - 4 * aa * cc < 0:
        return np.array([]), np.array([])

    one = (-bb + np.sqrt(bb**2 - 4 * aa * cc)) / (2 * aa)
    two = (-bb - np.sqrt(bb**2 - 4 * aa * cc)) / (2 * aa)
    points = np.array([one, two])
    seconds = np.sign(2 * aa * points + bb)

    return points, seconds

def findextremes(intercept, coeffs, offsets):
    # Finds where intercept + sum(3 coeffs[i] (x - offsets[i])^2) = 0
    coeffs = np.array(coeffs)
    offsets = np.array(offsets)
    aa = np.sum(3 * coeffs)
    bb = np.sum(-6 * coeffs * offsets)
    cc = intercept + np.sum(3 * coeffs * (offsets**2))

    return quadratic(aa, bb, cc)

def findminmaxwithin(intercept, coeffs, offsets, minx, maxx):
    points, seconds = findextremes(intercept, coeffs, offsets)
    if len(points) == 0:
        return points, points

    return (points[(seconds > 0) * (points >= minx) * (points <= maxx)],
            points[(seconds < 0) * (points >= minx) * (points <= maxx)])

def findsplineminmax(knots, coeffs, minx, maxx):
    allpoints = []
    knotKm1 = ([], []) # coeffs, offsets for x > knots[-2]
    knotK = ([], []) # coeffs, offsets for x > knots[-1]
    for kk in range(1, len(knots)-1):
        minp, maxp = findminmaxwithin(coeffs[0], coeffs[1:kk+1], knots[0:kk], knots[kk-1], knots[kk])
        allpoints.extend(minp)
        allpoints.extend(maxp)

        knotKm1[0].extend([coeffs[kk], -coeffs[kk] * (knots[-1] - knots[kk-1]) / (knots[-1] - knots[-2])])
        knotKm1[1].extend([knots[kk-1], knots[-2]])
        knotK[0].extend([coeffs[kk], -coeffs[kk] * (knots[-1] - knots[kk-1]) / (knots[-1] - knots[-2]), coeffs[kk] * (knots[-2] - knots[kk-1]) / (knots[-1] - knots[-2])])
        knotK[1].extend([knots[kk-1], knots[-2], knots[-1]])

    minp, maxp = findminmaxwithin(coeffs[0], knotKm1[0], knotKm1[1], knots[-2], knots[-1])
    allpoints.extend(minp)
    allpoints.extend(maxp)
    minp, maxp = findminmaxwithin(coeffs[0], knotK[0], knotK[1], knots[-1], np.inf)
    allpoints.extend(minp)
    allpoints.extend(maxp)

    allpoints.extend(knots) # Could also be edge-points

    # Drop all poitns outside of range
    allpoints = np.array(allpoints)
    allpoints = list(allpoints[(allpoints > minx) * (allpoints < maxx)])
    allpoints.extend([minx, maxx])

    # Determine the true lowest and highest
    curve = CubicSplineCurve(knots, coeffs)
    y = curve(np.array(allpoints))
    minpt = np.argmin(y)
    maxpt = np.argmax(y)

    return allpoints[minpt], allpoints[maxpt]

def findsplinemin(*args, **kwargs):
    x, _ = findsplineminmax(*args, **kwargs)
    return x

def findsplinemax(*args, **kwargs):
    _, x = findsplineminmax(*args, **kwargs)
    return x
