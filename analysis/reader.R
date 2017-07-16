library(ncdf4)

region.index <- NULL

get.variable <- function(filepath, variable) {
    nc <- nc_open(filepath)
    data <- ncvar_get(nc, variable)
    nc_close(nc)

    return(data)
}

get.variable.region <- function(filepath, variable, region=NULL) {
    nc <- nc_open(filepath)
    data <- ncvar_get(nc, variable)
    regions <- ncvar_get(nc, 'regions')
    nc_close(nc)

    if (length(dim(data)) == 1)
        return(data)

    if (is.null(region))
        return(data[region.index,])
    else {
        region.index <<- which(regions == region)
        return(data[regions == region,])
    }
}

get.relative <- function(targetdir, basename, suffix, fileregion, use.costs.region) {
    adapted <- 1e5 * get.variable.region(file.path(targetdir, paste0(basename, suffix, ".nc4")), 'rebased', fileregion)
    histclim <- 1e5 * get.variable.region(file.path(targetdir, paste0(basename, "-histclim", suffix, ".nc4")), 'rebased', fileregion)
    if (!is.null(use.costs.region)) {
        if (use.costs.region) {
            costs.lb <- get.variable.region(file.path(costs.targetdir, paste0(basename, "-costs", suffix, ".nc4")), 'costs_lb', fileregion)
            costs.ub <- get.variable.region(file.path(costs.targetdir, paste0(basename, "-costs", suffix, ".nc4")), 'costs_ub', fileregion)
        } else {
            costs.lb <- get.variable.region(file.path(costs.targetdir, paste0(basename, "-costs", suffix, ".nc4")), 'costs_lb')
            costs.ub <- get.variable.region(file.path(costs.targetdir, paste0(basename, "-costs", suffix, ".nc4")), 'costs_ub')
        }

        df <- data.frame(year=rep(years, 2),
                         values=c(adapted - histclim, adapted - histclim + (costs.lb + costs.ub) / 2),
                         model=rep(c('Fully adapted', 'Adaptation + Costs'), each=length(years)))

        costs.df <- data.frame(year=years, model="Upper and lower cost bounds", ymin=adapted - histclim + pmin(costs.lb, costs.ub), ymax=adapted - histclim + pmax(costs.lb, costs.ub))
        costs.gg <- ggplot_build(ggplot(costs.df, aes(x=year)) +
                stat_smooth(aes(y=ymin, colour='min'), se=F, span=.1) +
                stat_smooth(aes(y=ymin, colour='max'), se=F, span=.1))
        costs.df.sm <- data.frame(year=costs.gg$data[[1]]$x, ymin=costs.gg$data[[1]]$y, ymax=costs.gg$data[[2]]$y)

        return(list(df=df, costs.df.sm=costs.df.sm))
    } else {
        df <- data.frame(year=years,
                         values=adapted - histclim,
                         model='Fully adapted')

        return(list(df=df))
    }
}