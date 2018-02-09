setwd("~/research/gcp/impact-common/analysis/demos")

mean.gdppc <- 17818.2
mean.tmean <- 14.72947

source("../from-csvv.R") # Reads and prints CSVVs
source("../plotting.R") # Plots response curves
source("../splines.R") # Evaluates splines

## Set up the temperature sampling
xx <- seq(-15, 40, length.out=100)

## Evaluate the median
yy.const <- read.csvv("global_interaction_splineNS_GMFD.csvv-part", paste0('term', 0:6), c('loggdppc', 'climtas'), c(log(mean.gdppc), mean.tmean), function(betas) pmax(-1e5, pmin(1e5, getspline(betas, xx) - getspline(betas, 20))), mciters=1)

## Evaluate uncertainty across nonant of covariates
ggmatrix(function(covarx, covary, xx) {
    read.csvv("global_interaction_splineNS_GMFD.csvv-part", paste0('term', 0:6), c('loggdppc', 'climtas'), c(log(covary), covarx), function(betas) pmax(-50, pmin(50, getspline(betas, xx) - getspline(betas, 20))), mciters=1000)
}, c(10, 20, 30), c(1800, 7300, 26000), c("10 deg. C", "20 deg. C", "30 deg. C"), c("$1,800", "$7,300", "$26,000"), xx, ylim=c(-20, 20))

## Print a latex table of the CSVV
print(latex.csvv("global_interaction_splineNS_GMFD.csvv-part"), include.rownames=F)
