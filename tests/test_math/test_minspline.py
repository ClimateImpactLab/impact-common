import numpy as np
import numpy.testing as npt
from impactcommon.math.minspline import findextremes, findsplinemin


def test_findextremes():
    """Basic findextremes output test"""
    expected_points = np.array([17.1985009, 22.55233808])
    expected_seconds = np.array([1.0, -1.0])

    points, seconds = findextremes(
        intercept=-0.088404222535054311,
        coeffs=[
            0.00044585141069226897,
            -0.0013680191382785048,
            0.0015570001425749581,
            -0.00014956629970445078,
            -0.0036869690281538109,
        ],
        offsets=[-12, -7, 0, 10, 18],
    )

    npt.assert_allclose(points, expected_points)
    npt.assert_allclose(seconds, expected_seconds)


def test_findsplinemin():
    """Simple test of findsplinemin output"""
    expected = 16.985656534045365

    actual = findsplinemin(
        knots=[-12, -7, 0, 10, 18, 23, 28, 33],
        coeffs=[
            -0.088404222535054311,
            0.00044585141069226897,
            -0.0013680191382785048,
            0.0015570001425749581,
            -0.00014956629970445078,
            -0.0036869690281538109,
            0.011688014471165964,
        ],
        minx=10,
        maxx=25,
    )

    npt.assert_allclose([actual], [expected])
