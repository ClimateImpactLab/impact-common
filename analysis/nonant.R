library(ggplot2)

nonant.predict <- function(model, z1s, z2s, xs, z1.name, z2.name, x.name) {
    nonant(function(z1, z2) {
        preddf <- data.frame(xs)
        preddf[, x.name] <- xs
        preddf[, z1.name] <- z1
        preddf[, z2.name] <- z2

        predict(model, preddf, interval='confidence')
    }, z1s, z2s)
}

nonant <- function(get.curveci, z1s, z2s) {
    z1.quants <- quantile(z1s, na.rm=T)
    z2.quants <- quantile(z2s, na.rm=T)

    nonant.quants(get.curveci, z1.quants, z2.quants)
}

nonant.quants <- function(get.curveci, z1.quants, z2.quants) {
    df <- data.frame()
    for (z1 in z1.quants)
        for (z2 in z2.quants) {
            subdf <- get.curveci(z1, z2)
            subdf$z1 <- z1
            subdf$z2 <- z2

            df <- rbind(df, subdf)
        }


    ggplot(df, aes(x)) +
        facet_grid(z1 ~ z2, scales="free_y") +
        geom_line(aes(y)) +
        geom_ribbon(aes(ymin=ymin, ymax=ymax), alpha=.4) +
        xlab("Temperature") + ylab("Death Rate") +
        scale_x_continuous(expand=c(0, 0)) + theme_minimal()
}

## Example
data(iris)
mod <- lm(Sepal.Length ~ Sepal.Width, data=iris)
nonant.predict(mod, iris$Species, iris$Petal.Length / iris$Petal.Width, )
