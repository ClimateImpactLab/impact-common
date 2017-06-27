library(ncdf4)

get.variable <- function(filepath, variable) {
    nc <- nc_open(filepath)
    data <- ncvar_get(nc, variable)
    nc_close(nc)

    return(data)
}

get.variable.region <- function(filepath, variable, region) {
    nc <- nc_open(filepath)
    data <- ncvar_get(nc, variable)
    regions <- ncvar_get(nc, 'regions')
    nc_close(nc)

    return(data[regions == region,])
}
