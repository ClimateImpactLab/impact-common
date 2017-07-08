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
