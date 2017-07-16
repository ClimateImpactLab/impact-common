library(ggplot2)
source("reader.R")

args = commandArgs(trailingOnly=TRUE)

if (args[1] == 'full') {
    targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp45/CSIRO-Mk3-6-0/low/SSP5"
    basename <- "global_interaction_Tmean-POLY-4-AgeSpec-combined"
    region <- "global"
    costs.targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp45/CSIRO-Mk3-6-0/low/SSP5"
    suffix <- '-aggregated'
    use.costs.region <- T
} else if (args[1] == 'diag') {
    targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/single-no-gm/rcp85/CCSM4/low/SSP4"
    basename <- "global_interaction_Tmean-POLY-4-AgeSpec-oldest"
    region <- "IND.33.542.2153"
    costs.targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/single-no-gm/rcp85/CCSM4/low/SSP4"
    suffix <- ''
    use.costs.region <- F
} else if (args[1] == 'indi') {
    targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp45/CSIRO-Mk3-6-0/low/SSP5"
    basename <- "global_interaction_Tmean-POLY-4-AgeSpec-combined"
    region <- "global"
    costs.targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp45/CSIRO-Mk3-6-0/low/SSP5"
    suffix <- '-indiamerge-aggregated'
    use.costs.region <- T
}

fileregion <- region
if (region == 'global')
    fileregion <- ''

years <- get.variable(file.path(targetdir, paste0(basename, suffix, ".nc4")), 'year')

adapted <- 1e5 * get.variable.region(file.path(targetdir, paste0(basename, suffix, ".nc4")), 'rebased', fileregion)
noadapt <- 1e5 * get.variable.region(file.path(targetdir, paste0(basename, "-noadapt", suffix, ".nc4")), 'rebased', fileregion)
incadapt <- 1e5 * get.variable.region(file.path(targetdir, paste0(basename, "-incadapt", suffix, ".nc4")), 'rebased', fileregion)
histclim <- 1e5 * get.variable.region(file.path(targetdir, paste0(basename, "-histclim", suffix, ".nc4")), 'rebased', fileregion)
if (!is.null(use.costs.region)) {
  if (use.costs.region) {
    costs.lb <- get.variable.region(file.path(costs.targetdir, paste0(basename, "-costs", suffix, ".nc4")), 'costs_lb', fileregion)
    costs.ub <- get.variable.region(file.path(costs.targetdir, paste0(basename, "-costs", suffix, ".nc4")), 'costs_ub', fileregion)
  } else {
    costs.lb <- get.variable.region(file.path(costs.targetdir, paste0(basename, "-costs", suffix, ".nc4")), 'costs_lb')
    costs.ub <- get.variable.region(file.path(costs.targetdir, paste0(basename, "-costs", suffix, ".nc4")), 'costs_ub')
  }

  df <- data.frame(year=rep(years, 4),
                   values=c(adapted - histclim, noadapt - c(histclim[years < 2015], rep(histclim[years == 2015], sum(years >= 2015))), incadapt - histclim, adapted - histclim + (costs.lb + costs.ub) / 2),
                   model=rep(c('Fully adapted', 'No adaptation', 'Income-only adaptation', 'Adaptation + Costs'), each=length(years)))

  costs.df <- data.frame(year=years, model="Upper and lower cost bounds", ymin=adapted - histclim + pmin(costs.lb, costs.ub), ymax=adapted - histclim + pmax(costs.lb, costs.ub))
  costs.gg <- ggplot_build(ggplot(costs.df, aes(x=year)) +
          stat_smooth(aes(y=ymin, colour='min'), se=F, span=.1) +
          stat_smooth(aes(y=ymin, colour='max'), se=F, span=.1))
  costs.df.sm <- data.frame(year=costs.gg$data[[1]]$x, ymin=costs.gg$data[[1]]$y, ymax=costs.gg$data[[2]]$y)

  print(tail(df))

  ggplot(df) + geom_smooth(aes(x=year, y=values, colour=model), se=F, span=.1) +
      geom_ribbon(data=costs.df.sm, aes(x=year, ymin=ymin, ymax=ymax, alpha="Upper and lower cost bounds")) +
      geom_hline(yintercept=0, size=.3) + scale_x_continuous(expand=c(0, 0), limits=c(2005, 2099)) +
      xlab("") + ylab("Heat and cold deaths per 100,000 per year") +
      scale_colour_manual(name="Model assumptions:", breaks=c("No adaptation", "Income-only adaptation", "Fully adapted", "Adaptation + Costs"), values=c("No adaptation"="#D55E00", "Income-only adaptation"="#E69F00", "Fully adapted"="#009E73", "Adaptation + Costs"="#000000")) +
      scale_alpha_manual(name="", values=.5) +
      ggtitle(paste("Comparison of mortality impacts by assumption, ", region)) +
      theme_bw() + theme(legend.justification=c(0,1), legend.position=c(0,1))
  ggsave("result.pdf", width=7, height=4)
} else {
  df <- data.frame(year=rep(years, 3),
                   values=c(adapted - histclim, noadapt - c(histclim[years < 2015], rep(histclim[years == 2015], sum(years >= 2015))), incadapt - histclim),
                   model=rep(c('Fully adapted', 'No adaptation', 'Income-only adaptation'), each=length(years)))

  pdf("result.pdf", width=7, height=4)
  ggplot(df) + geom_smooth(aes(x=year, y=values, colour=model), se=F, span=.1) +
      geom_hline(yintercept=0, size=.3) + scale_x_continuous(expand=c(0, 0), limits=c(2005, 2099)) +
      xlab("") + ylab("Heat and cold deaths per 100,000 per year") +
      scale_colour_manual(name="Model assumptions:", breaks=c("No adaptation", "Income-only adaptation", "Fully adapted", "Adaptation + Costs"), values=c("No adaptation"="#D55E00", "Income-only adaptation"="#E69F00", "Fully adapted"="#009E73")) +
      scale_alpha_manual(name="", values=.5) +
      ggtitle(paste("Comparison of mortality impacts by assumption, ", region)) +
      theme_bw() + theme(legend.justification=c(0,1), legend.position=c(0,1))
  dev.off()

}    
