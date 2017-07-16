library(ggplot2)
source("reader.R")

args = commandArgs(trailingOnly=TRUE)

if (args[1] == 'indi') {
    targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp45/CSIRO-Mk3-6-0/low/SSP5"
    basename1 <- "global_interaction_Tmean-POLY-4-AgeSpec-combined"
    basename2 <- "global_interaction_Tmean-POLY-4-AgeSpec-combined"
    region <- "global"
    costs.targetdir <- "/shares/gcp/outputs/mortality/impacts-crypto/median/rcp45/CSIRO-Mk3-6-0/low/SSP5"
    suffix1 <- '-aggregated'
    suffix2 <- '-indiamerge-aggregated'
    use.costs.region <- T
    name1 <- "Combined Ages"
    name2 <- "Post-India Merge"
}

fileregion <- region
if (region == 'global')
    fileregion <- ''

years <- get.variable(file.path(targetdir, paste0(basename1, suffix1, ".nc4")), 'year')

data1 <- get.relative(targetdir, basename1, suffix1, fileregion, use.costs.region)
data2 <- get.relative(targetdir, basename2, suffix2, fileregion, use.costs.region)
if (!is.null(use.costs.region)) {
  df1 <- data1[["df"]]
  df1$year <- rep(years, 2)
  costs.df.sm1 <- data1[["costs.df.sm"]]
  df1$name <- name1
  costs.df.sm1$name <- name1

  df2 <- data2[["df"]]
  df2$year <- rep(years, 2)
  costs.df.sm2 <- data2[["costs.df.sm"]]
  df2$name <- name2
  costs.df.sm2$name <- name2

  ggplot(rbind(df1, df2)) + geom_smooth(aes(x=year, y=values, colour=model, linetype=name), se=F, span=.1) +
      geom_ribbon(data=rbind(costs.df.sm1, costs.df.sm2), aes(x=year, ymin=ymin, ymax=ymax, alpha="Upper and lower cost bounds", group=name)) +
      geom_hline(yintercept=0, size=.3) + scale_x_continuous(expand=c(0, 0), limits=c(2005, 2099)) +
      xlab("") + ylab("Heat and cold deaths per 100,000 per year") +
      scale_colour_manual(name="Model assumptions:", breaks=c("Fully adapted", "Adaptation + Costs"), values=c("Fully adapted"="#009E73", "Adaptation + Costs"="#000000")) +
      scale_alpha_manual(name="", values=.5) +
      ggtitle(paste("Comparison of mortality impacts by assumption, ", region)) +
      theme_bw() + scale_linetype_discrete(name="")
  ggsave("result.pdf", width=7, height=4)
} else {
  df1 <- data1[["df"]]
  df1$year <- year
  df1$name <- name1

  df2 <- data2[["df"]]
  df2$year <- year
  df2$name <- name2

  pdf("result.pdf", width=7, height=4)
  ggplot(rbind(df1, df2)) + geom_smooth(aes(x=year, y=values, colour=model, linetype=name), se=F, span=.1) +
      geom_hline(yintercept=0, size=.3) + scale_x_continuous(expand=c(0, 0), limits=c(2005, 2099)) +
      xlab("") + ylab("Heat and cold deaths per 100,000 per year") +
      scale_colour_manual(name="Model assumptions:", breaks=c("Fully adapted"), values=c("Fully adapted"="#009E73")) +
      scale_alpha_manual(name="", values=.5) +
      ggtitle(paste("Comparison of mortality impacts by assumption, ", region)) +
      theme_bw() + theme(legend.justification=c(0,1), legend.position=c(0,1))
  dev.off()
}    
