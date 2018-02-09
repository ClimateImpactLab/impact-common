library(MASS)
library(xtable)

####
## Read a CSVV and evaluate it at the given covariate levels.
## Uncertainty is evaluated across a set of Monte Carlos
## Arguments:
## myprednames: the list of the predictor names for which betas should be calculated
## mycovarnames: the list of covariate names to be included
##   Don't include '1' in mycovarnames
## covars: the values of the covariates in `mycovarnames`
## evalpts: A function which returns the curve for a given set of betas
## If mciters = 1, returns the median as a vector
## Otherwise, returns a table with columns for each of the quantiles in `probs` (by default, .025, .5, .975)
####
read.csvv <- function(filepath, myprednames, mycovarnames, covars, evalpts, mciters=1000, probs=c(.025, .5, .975)) {
    fp <- file(filepath, "r")
    while (T) {
        line = readLines(fp, n=1)
        if (length(line) == 0)
            break

        if (line == 'prednames')
            prednames <- strsplit(readLines(fp, n=1), ',')[[1]]
        if (line == 'covarnames')
            covarnames <- strsplit(readLines(fp, n=1), ',')[[1]]
        if (line == 'gamma')
            gamma <- as.numeric(strsplit(readLines(fp, n=1), ',')[[1]])
        if (line == 'gammavcv')
            gammavcv <- t(sapply(strsplit(readLines(fp, n=length(gamma)), ','), as.numeric))
    }
    close(fp)

    ## Generate MC draws from beta(covars)
    if (mciters == 1)
        gammas <- matrix(gamma, 1, length(gamma)) # Give median
    else
        gammas <- mvrnorm(mciters, gamma, gammavcv)
    betas <- data.frame(iter=1:mciters)
    for (predname in myprednames) {
        predtotal <- gammas[, prednames == predname & covarnames == '1']
        for (ll in 1:length(mycovarnames))
            predtotal <- predtotal + gammas[, prednames == predname & covarnames == mycovarnames[ll]] * covars[ll]
        betas[, predname] <- predtotal
    }
    betas <- as.matrix(betas[,-1])

    ## Determine the confidence intervals
    allpoints <- evalpts(betas[1,])
    if (mciters > 1) {
        for (ii in 2:mciters)
            allpoints <- rbind(allpoints, evalpts(betas[ii,]))
    }

    if (mciters == 1)
        allpoints
    else
        apply(allpoints, 2, function(col) quantile(col, probs=probs))
}

####
## Read a CSVV and print it as a simple regression table.
####
latex.csvv <- function(filepath, digits=4) {
    fp <- file(filepath, "r")
    while (T) {
        line = readLines(fp, n=1)
        if (length(line) == 0)
            break

        if (line == 'prednames')
            prednames <- strsplit(readLines(fp, n=1), ',')[[1]]
        if (line == 'covarnames')
            covarnames <- strsplit(readLines(fp, n=1), ',')[[1]]
        if (line == 'gamma')
            gamma <- as.numeric(strsplit(readLines(fp, n=1), ',')[[1]])
        if (line == 'gammavcv')
            gammavcv <- t(sapply(strsplit(readLines(fp, n=length(gamma)), ','), as.numeric))
    }
    close(fp)

    df <- data.frame(variable=c(), gamma=c(), stderr=c())
    for (predname in unique(prednames))
        for (covarname in unique(covarnames)) {
            if (covarname == '1')
                variable <- predname
            else
                variable <- paste(predname, covarname, sep=':')

            kk <- which(prednames == predname & covarnames == covarname)
            df <- rbind(df, data.frame(variable, gamma[kk], paste0('(', format(sqrt(gammavcv[kk, kk]), digits=digits), ')')))
        }

    names(df) <- c("Variable", "Gamma", "Std. Err.")
    xtable(df, digits=digits)
}
