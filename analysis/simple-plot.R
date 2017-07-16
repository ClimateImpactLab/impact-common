library(ggplot2)
source("reader.R")

args = commandArgs(trailingOnly=TRUE)

if (args[1] == 'full') {
    targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp85/CCSM4/high/SSP4"
    basename <- "global_interaction_Tmean-POLY-4-AgeSpec-combined"
    region <- "global"
    costs.targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp85/CCSM4/high/SSP4"
    suffix <- '-aggregated'
    use.costs.region <- T
} else if (args[1] == 'diag') {
    targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/single-no-gm/rcp85/CCSM4/low/SSP4" #args[1]
    basename <- "global_interaction_Tmean-POLY-4-AgeSpec-oldest" #args[2]
    region <- "IND.33.542.2153" #args[3]
    costs.targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/single-no-gm/rcp85/CCSM4/low/SSP4"
    suffix <- ''
    use.costs.region <- F
} else if (args[1] == 'indi') {
    targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp45/CSIRO-Mk3-6-0/low/SSP5"
    basename1 <- "global_interaction_Tmean-POLY-4-AgeSpec-combined"
    basename2 <- "global_interaction_Tmean-POLY-4-AgeSpec-combined-indiamerge"
    region <- "global"
    costs.targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp45/CSIRO-Mk3-6-0/low/SSP5"
    suffix1 <- '-aggregated'
    suffix2 <- '-indiamerge-aggregated'
    use.costs.region <- T
}

fileregion <- region
if (region == 'global')
    fileregion <- ''

years <- get.variable(file.path(targetdir, paste0(basename, suffix, ".nc4")), 'year')

data <- get.relative(targetdir, basename, suffix, fileregion, use.costs.region)
if (!is.null(use.costs.region)) {
  df <- data[["df"]]
  df$year <- rep(years, 2)
  costs.df.sm <- data[["costs.df.sm"]]

  pdf("result.pdf", width=7, height=4)
  ggplot(df) + geom_smooth(aes(x=year, y=values, colour=model), se=F, span=.1) +
      geom_ribbon(data=costs.df.sm, aes(x=year, ymin=ymin, ymax=ymax, alpha="Upper and lower cost bounds")) +
      geom_hline(yintercept=0, size=.3) + scale_x_continuous(expand=c(0, 0), limits=c(2005, 2099)) +
      xlab("") + ylab("Heat and cold deaths per 100,000 per year") +
      scale_colour_manual(name="Model assumptions:", breaks=c("Fully adapted", "Adaptation + Costs"), values=c("Fully adapted"="#009E73", "Adaptation + Costs"="#000000")) +
      scale_alpha_manual(name="", values=.5) +
      ggtitle(paste("Comparison of mortality impacts by assumption, ", region)) +
      theme_bw() + theme(legend.justification=c(0,1), legend.position=c(0,1))
  dev.off()
} else {
  df <- data[["df"]]
  df$year <- year

  pdf("result.pdf", width=7, height=4)
  ggplot(df) + geom_smooth(aes(x=year, y=values, colour=model), se=F, span=.1) +
      geom_hline(yintercept=0, size=.3) + scale_x_continuous(expand=c(0, 0), limits=c(2005, 2099)) +
      xlab("") + ylab("Heat and cold deaths per 100,000 per year") +
      scale_colour_manual(name="Model assumptions:", breaks=c("Fully adapted"), values=c("Fully adapted"="#009E73")) +
      scale_alpha_manual(name="", values=.5) +
      ggtitle(paste("Comparison of mortality impacts by assumption, ", region)) +
      theme_bw() + theme(legend.justification=c(0,1), legend.position=c(0,1))
  dev.off()

}    
