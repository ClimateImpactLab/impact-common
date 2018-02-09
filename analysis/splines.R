## Evaluate a cubic spline function with the given coefficients
getspline <- function(coeffs, xx) {
    knots <- c(-12, -7, 0, 10, 18, 23, 28, 33)

    pos <- function(xx) xx * (xx > 0)

    total <- coeffs[1] * xx
    for (kk in 1:(length(coeffs)-2)) {
        xterm <- pos(xx - knots[kk])^3 - pos(xx - knots[length(knots)-1])^3 * (knots[length(knots)] - knots[kk]) / (knots[length(knots)] - knots[length(knots) - 1]) + pos(xx - knots[length(knots)])^3 * (knots[length(knots)-1] - knots[kk]) / (knots[length(knots)] - knots[length(knots) - 1])
        total <- total + coeffs[kk+1] * xterm
    }

    total
}
