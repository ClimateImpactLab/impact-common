library(ggplot2)

## These functions return ggplot objects, to which additional drawing features can be added.

## A simple curve with confidence intervals
## allpoints is a table with columns for the .025, .5, .975 quantiles
## The length of `xx`, the x-axis points, should equal the number of rows of `allpoints`.
ggstandard <- function(allpoints, xx) {
    ggplot(data.frame(x=xx, y=allpoints[2,], ymin=allpoints[1,], ymax=allpoints[3,]), aes(x, y, ymin=ymin, ymax=ymax)) +
        geom_line() + geom_ribbon(alpha=.5) +
        xlab("Temperature") + ylab("Regular response") + theme_bw() +
        scale_x_continuous(expand=c(0, 0)) + scale_y_continuous(expand=c(0, 0))
}

## A simple curve without uncertainty
## Like ggstandard, but without confidence intervals
## yy should be a vector the same length as xx
ggmedian <- function(yy, xx) {
    ggplot(data.frame(x=xx, y=yy), aes(x, y)) +
        geom_line() +
        xlab("Temperature") + ylab("Regular response") + theme_bw() +
        scale_x_continuous(expand=c(0, 0)) + scale_y_continuous(expand=c(0, 0))
}

## A comparison between two curves
## A combination of ggstandard, giving a confidence interval from the data in allpoints,
##   and ggmedian, showing the median curve for some comparison
ggcompare <- function(allpoints, yy.base, xx) {
    ggplot(data.frame(x=rep(xx, 2), y=c(allpoints[2,], yy.base), ymin=c(allpoints[1,], yy.base), ymax=c(allpoints[3,], yy.base), group=rep(c('full', 'base'), each=length(xx))), aes(x, y, group=group)) +
        geom_ribbon(aes(ymin=ymin, ymax=ymax), alpha=.5) +
        geom_line(aes(colour=group)) +
        xlab("Temperature") + ylab("Regular response") + theme_bw() +
        scale_colour_discrete(name="Assumptions:", breaks=c('base', 'full'), labels=c("Standard", "Geographic")) + theme(legend.position="bottom")
}

## A nonant matrix
## Produces a NxM matrix of graphs evaluated at the given covariates.
## `generate` is a function of the columns covariate, rows covariate, and x-axis values,
##   and shuold return a matrix like the one used in ggstandard.
## `covarxs` and `covarys` are the values of the column and row covariates.
## `covarxlabs` and `covarylabs` are the corresponding labels
## `xx` is a vector of x-axis values
## `ylim` limits the y-axis.
ggmatrix <- function(generate, covarxs, covarys, covarxlabs, covarylabs, xx, ylim=NULL) {
    df <- rbind(x=c(), y=c(), ymin=c(), ymax=c(), covarx=c(), covary=c(), group=c())
    for (covarx in covarxs) {
        for (covary in covarys) {
            print(c(covarx, covary))
            allpoints <- generate(covarx, covary, xx)
            df <- rbind(df, data.frame(x=xx, y=allpoints[2,], ymin=allpoints[1,], ymax=allpoints[3,], covarx=covarxlabs[covarxs == covarx], covary=covarylabs[covarys == covary]))
        }
    }

    plot <- ggplot(df, aes(x, y)) +
        facet_grid(covary ~ covarx) +
        geom_ribbon(aes(ymin=ymin, ymax=ymax), alpha=.5) +
        geom_line() +
        xlab("Temperature") + ylab("Regular response") + theme_bw() +
        scale_x_continuous(expand=c(0, 0)) + scale_y_continuous(expand=c(0, 0))
    if (!is.null(ylim))
        plot <- plot + coord_cartesian(ylim=ylim)

    plot
}

## A comparison between two curves in a nonant matrix
## Like ggcompare, but for nonants.  Arguments are the same as `ggmatrix`,
##   but take a second `generate` function, which should return a vector of values.
ggmatrixcompare <- function(generate.full, generate.base, covarxs, covarys, covarxlabs, covarylabs, xx) {
    df <- rbind(x=c(), y=c(), ymin=c(), ymax=c(), covarx=c(), covary=c(), group=c())
    for (covarx in covarxs) {
        for (covary in covarys) {
            print(c(covarx, covary))
            allpoints <- generate.full(covarx, covary, xx)
            yy.base <- generate.base(covarx, covary, xx)
            df <- rbind(df, data.frame(x=rep(xx, 2), y=c(allpoints[2,], yy.base), ymin=c(allpoints[1,], yy.base), ymax=c(allpoints[3,], yy.base), group=rep(c('full', 'base'), each=length(xx)), covarx=covarxlabs[covarxs == covarx], covary=covarylabs[covarys == covary]))
        }
    }

    ggplot(df, aes(x, y, group=paste(group, covarx, covary))) +
        facet_grid(covary ~ covarx) +
        geom_ribbon(aes(ymin=ymin, ymax=ymax), alpha=.5) +
        geom_line(aes(colour=group)) +
        xlab("Temperature") + ylab("Regular response") + theme_bw() +
        scale_colour_discrete(name="Assumptions:", breaks=c('base', 'full'), labels=c("Standard", "Geographic")) + theme(legend.position="bottom") +
        scale_x_continuous(expand=c(0, 0)) + scale_y_continuous(expand=c(0, 0))
}
