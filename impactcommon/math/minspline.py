######
# These functions calculate the minimum of a cubic spline.
# The main function is `findsplinemin`.
######

## Find minimum of expression of the form intercept x + sum(coeffs[i] (x - offsets[i])^3)

# For legacy purpose
from impactcommon.math.minmaxspline import findsplinemin, findextremes


if __name__ == '__main__':
    print(findextremes(-0.088404222535054311, [0.00044585141069226897, -0.0013680191382785048, 0.0015570001425749581, -0.00014956629970445078, -0.0036869690281538109], [-12, -7, 0, 10, 18]))
    print(findsplinemin([-12, -7, 0, 10, 18, 23, 28, 33], [-0.088404222535054311, 0.00044585141069226897, -0.0013680191382785048, 0.0015570001425749581, -0.00014956629970445078, -0.0036869690281538109, 0.011688014471165964], 10, 25))
