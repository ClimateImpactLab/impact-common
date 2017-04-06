rm(list = ls())
#rm(list= ls()[!(ls() %in% c('positive','twofactors.two.full.dd.thirty.ten.linc2'))])


#load packages
library(lfe)
library(msm)
library(texreg)
library(ggplot2)
library(reshape2)
library(data.table)
library(readstata13)
library(plyr)
library(dplyr)



#set working directory
setwd("/Users/trinettachong/Dropbox/Global ACP/ClimateLaborGlobalPaper/Paper/Datasets/")
#####################################
#load stata dataset
timetoload <- proc.time()
dat <- read.dta13("Trin_test/labor_popop_income_dd_6mar.dta")
proc.time() - timetoload

#limit data to observations with mins_worked>0
positive <- subset(dat,mins_worked > 0)

#remove all observations in MEX
positive <- subset(positive, country !=7)

#check that country==7 was removed
table(positive$country)

#create inc2 variable
positive <- transform(positive,lnincomeLP2 = lnincomeLP*lnincomeLP)
names(positive)
                    
#regression with lninc^2
timereg <- proc.time()
#regression (excluding MEX) - constrained (30/10)
twofactors.two.full.dd.thirty.ten.linc2 <- with(positive,felm(mins_worked ~ tempL0 + temp2L0 + temp3L0 + temp4L0 
                                                        + lnincomeLP:tempL0 + lnincomeLP:temp2L0 + lnincomeLP:temp3L0 + lnincomeLP:temp4L0 
                                                        + hotdd_30:tempL0_27nabove + hotdd_30:temp2L0_27nabove + hotdd_30:temp3L0_27nabove + hotdd_30:temp4L0_27nabove
                                                        + colddd_10:tempL0_below27 + colddd_10:temp2L0_below27 + colddd_10:temp3L0_below27 + colddd_10:temp4L0_below27
                                                        + lnincomeLP2:tempL0 + lnincomeLP2:temp2L0 + lnincomeLP2:temp3L0 + lnincomeLP2:temp4L0 
                                                        + age + age2 + male + hhsize + belowzero|as.factor(location_id1)*as.factor(year)*as.factor(month)+as.factor(location_id2)+as.factor(dow_week)|0|cluster,weight=pop_weight))
proc.time() - timereg


######################################

#save results
save.image("Trin_test/new_constrained_2factorcode_2_full_dd_30_10_lninc2")

load("Trin_test/new_constrained_2factorcode_2_full_dd_30_10_lninc2")
######################################

#see summary of estimates
summary(twofactors.two.full.dd.thirty.ten.linc2)

#create vector of temperatures (-18C to 44 C and recode below0 temps with 0)
t0 = -18
temps <- seq(t0,44,1)
as.data.frame(temps)
temps[temps<=0] <- 0

#create full temp vector (-18 to 44)
temps_full <- seq(-18,44,1)
temp27 <- rep(27,63)

##############################
#for income
############################

#extract regression coefficients
cf <- summary(twofactors.two.full.dd.thirty.ten.linc2)$coef

linc <- quantile(positive$lnincomeLP, c(.05), na.rm = TRUE) 
print(linc)

minc <-  quantile(positive$lnincomeLP, c(.5), na.rm = TRUE)
print(minc)

hinc <- quantile(positive$lnincomeLP, c(.95), na.rm = TRUE)
print(hinc)


#5 pct
#unnormalized response vector
resp <- cf['tempL0:lnincomeLP',1]*temps + cf['temp2L0:lnincomeLP',1]*temps^2 + cf['temp3L0:lnincomeLP',1]*temps^3 + cf['temp4L0:lnincomeLP',1]*temps^4 + ((2*linc) + 1)*(cf['tempL0:lnincomeLP2',1]*temps + cf['temp2L0:lnincomeLP2',1]*temps^2 + cf['temp3L0:lnincomeLP2',1]*temps^3 + cf['temp4L0:lnincomeLP2',1]*temps^4)
resp27 <- cf['tempL0:lnincomeLP',1]*temp27 + cf['temp2L0:lnincomeLP',1]*temp27^2 + cf['temp3L0:lnincomeLP',1]*temp27^3 + cf['temp4L0:lnincomeLP',1]*temp27^4 + ((2*linc) + 1)*(cf['tempL0:lnincomeLP2',1]*temp27 + cf['temp2L0:lnincomeLP2',1]*temp27^2 + cf['temp3L0:lnincomeLP2',1]*temp27^3 + cf['temp4L0:lnincomeLP2',1]*temp27^4)
lo.respnorm <- resp - resp27

#calculate se for each temperature and put it in a vector
se <- 0
#loop over each temp from -18 to -1
for (z in 1:18) {
  se[z] <- deltamethod(~ x10*(0-27) + x11*(0-(27^2)) + x12*(0-(27^3)) + x13*(0-(27^4)) + ((2*linc) + 1)*(x22*(0-27) + x23*(0-(27^2)) + x24*(0-(27^3)) + x25*(0-(27^4))), coef(twofactors.two.full.dd.thirty.ten.linc2), vcov(twofactors.two.full.dd.thirty.ten.linc2))
} 
#loop over each temp from 0 to 44
for (z in 19:63) {
  se[z] <- deltamethod(~ x10*((z-19)-27) + x11*((z-19)^2-27^2) + x12*((z-19)^3-27^3) + x13*((z-19)^4-27^4) + ((2*linc) + 1)*(x22*((z-19)-27) + x23*((z-19)^2-27^2) + x24*((z-19)^3-27^3) + x25*((z-19)^4-27^4)), coef(twofactors.two.full.dd.thirty.ten.linc2), vcov(twofactors.two.full.dd.thirty.ten.linc2))
}
#view se vector
print(se)
#confidence intervals
lo.lowerci = lo.respnorm - (1.96*se)
lo.upperci = lo.respnorm + (1.96*se)

#plot
resp.df <- data.frame(temps, lo.respnorm, lo.lowerci, lo.upperci)
p <- ggplot(data=resp.df, aes(x=temps, y=lo.respnorm)) + geom_line(colour = "steelblue3") + 
  geom_ribbon(aes(ymin=resp.df$lo.lowerci, ymax=resp.df$lo.upperci), fill = "steelblue2", linetype=2, alpha=0.3) +
  theme_bw() +
  theme(panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(), 
        axis.line = element_line(colour = "black")) +
  xlab("Temperature") + ylab("Change in mins worked relative to 27C") +
  coord_cartesian(ylim = c(-130,200), xlim =c(0,44))  +
  ggtitle("2 Factor Interaction (Low income) (Full Sample, state x MOS FEs)")
ggsave(p, file="Trin_test/2factor_2_full_inc2_lo.png")


#50 pct
#unnormalized response vector
resp <- cf['tempL0:lnincomeLP',1]*temps + cf['temp2L0:lnincomeLP',1]*temps^2 + cf['temp3L0:lnincomeLP',1]*temps^3 + cf['temp4L0:lnincomeLP',1]*temps^4 + ((2*minc) + 1)*(cf['tempL0:lnincomeLP2',1]*temps + cf['temp2L0:lnincomeLP2',1]*temps^2 + cf['temp3L0:lnincomeLP2',1]*temps^3 + cf['temp4L0:lnincomeLP2',1]*temps^4)
resp27 <- cf['tempL0:lnincomeLP',1]*temp27 + cf['temp2L0:lnincomeLP',1]*temp27^2 + cf['temp3L0:lnincomeLP',1]*temp27^3 + cf['temp4L0:lnincomeLP',1]*temp27^4 + ((2*minc) + 1)*(cf['tempL0:lnincomeLP2',1]*temp27 + cf['temp2L0:lnincomeLP2',1]*temp27^2 + cf['temp3L0:lnincomeLP2',1]*temp27^3 + cf['temp4L0:lnincomeLP2',1]*temp27^4)
mid.respnorm <- resp - resp27

#calculate se for each temperature and put it in a vector
se <- 0
for (z in 1:18) {
  se[z] <- deltamethod(~ x10*(0-27) + x11*(0-(27^2)) + x12*(0-(27^3)) + x13*(0-(27^4)) + ((2*minc) + 1)*(x22*(0-27) + x23*(0-(27^2)) + x24*(0-(27^3)) + x25*(0-(27^4))), coef(twofactors.two.full.dd.thirty.ten.linc2), vcov(twofactors.two.full.dd.thirty.ten.linc2))
} 
#loop over each temp from 0 to 44
for (z in 19:63) {
  se[z] <- deltamethod(~ x10*((z-19)-27) + x11*((z-19)^2-27^2) + x12*((z-19)^3-27^3) + x13*((z-19)^4-27^4) + ((2*minc) + 1)*(x22*((z-19)-27) + x23*((z-19)^2-27^2) + x24*((z-19)^3-27^3) + x25*((z-19)^4-27^4)), coef(twofactors.two.full.dd.thirty.ten.linc2), vcov(twofactors.two.full.dd.thirty.ten.linc2))
}
#view se vector
print(se)
#confidence intervals
mid.lowerci = mid.respnorm - (1.96*se)
mid.upperci = mid.respnorm + (1.96*se)

#plot
resp.df <- data.frame(temps, mid.respnorm, mid.lowerci, mid.upperci)
p <- ggplot(data=resp.df, aes(x=temps, y=mid.respnorm)) + geom_line(colour = "steelblue3") + 
  geom_ribbon(aes(ymin=resp.df$mid.lowerci, ymax=resp.df$mid.upperci), fill = "steelblue2", linetype=2, alpha=0.3) +
  theme_bw() +
  theme(panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(), 
        axis.line = element_line(colour = "black")) +
  xlab("Temperature") + ylab("Change in mins worked relative to 27C") +
  coord_cartesian(ylim = c(-130,200), xlim =c(0,44))  +
    ggtitle("2 Factor Interaction (Mid income) (Full Sample, state x MOS FEs)")
ggsave(p, file="Trin_test/2factor_2_full_inc2_mid.png")


#90 pct
#unnormalized response vector
resp <- cf['tempL0:lnincomeLP',1]*temps + cf['temp2L0:lnincomeLP',1]*temps^2 + cf['temp3L0:lnincomeLP',1]*temps^3 + cf['temp4L0:lnincomeLP',1]*temps^4 + ((2*hinc) + 1)*(cf['tempL0:lnincomeLP2',1]*temps + cf['temp2L0:lnincomeLP2',1]*temps^2 + cf['temp3L0:lnincomeLP2',1]*temps^3 + cf['temp4L0:lnincomeLP2',1]*temps^4)
resp27 <- cf['tempL0:lnincomeLP',1]*temp27 + cf['temp2L0:lnincomeLP',1]*temp27^2 + cf['temp3L0:lnincomeLP',1]*temp27^3 + cf['temp4L0:lnincomeLP',1]*temp27^4 + ((2*hinc) + 1)*(cf['tempL0:lnincomeLP2',1]*temp27 + cf['temp2L0:lnincomeLP2',1]*temp27^2 + cf['temp3L0:lnincomeLP2',1]*temp27^3 + cf['temp4L0:lnincomeLP2',1]*temp27^4)
hi.respnorm <- resp - resp27

#calculate se for each temperature and put it in a vector
se <- 0
#loop over each temp from -18 to -1
for (z in 1:18) {
  se[z] <- deltamethod(~ x10*(0-27) + x11*(0-(27^2)) + x12*(0-(27^3)) + x13*(0-(27^4)) + ((2*hinc) + 1)*(x22*(0-27) + x23*(0-(27^2)) + x24*(0-(27^3)) + x25*(0-(27^4))), coef(twofactors.two.full.dd.thirty.ten.linc2), vcov(twofactors.two.full.dd.thirty.ten.linc2))
} 
#loop over each temp from 0 to 44
for (z in 19:63) {
  se[z] <- deltamethod(~ x10*((z-19)-27) + x11*((z-19)^2-27^2) + x12*((z-19)^3-27^3) + x13*((z-19)^4-27^4) + ((2*hinc) + 1)*(x22*((z-19)-27) + x23*((z-19)^2-27^2) + x24*((z-19)^3-27^3) + x25*((z-19)^4-27^4)), coef(twofactors.two.full.dd.thirty.ten.linc2), vcov(twofactors.two.full.dd.thirty.ten.linc2))
}
#view se vector
print(se)
#confidence intervals
hi.lowerci = hi.respnorm - (1.96*se)
hi.upperci = hi.respnorm + (1.96*se)

#plot
resp.df <- data.frame(temps, hi.respnorm, hi.lowerci, hi.upperci)
p <- ggplot(data=resp.df, aes(x=temps, y=hi.respnorm)) + geom_line(colour = "steelblue3") + 
  geom_ribbon(aes(ymin=resp.df$hi.lowerci, ymax=resp.df$hi.upperci), fill = "steelblue2", linetype=2, alpha=0.3) +
  theme_bw() +
  theme(panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(), 
        axis.line = element_line(colour = "black")) +
  xlab("Temperature") + ylab("Change in mins worked relative to 27C") +
  coord_cartesian(ylim = c(-130,200), xlim =c(0,44))  +
  ggtitle("2 Factor Interaction (High income) (Full Sample, state x MOS FEs)")
ggsave(p, file="Trin_test/2factor_2_full_inc2_hi.png")


#plot beta at 3 different levels
inc2beta <- data.frame(temps, lo.respnorm, mid.respnorm, hi.respnorm)
#reshape from wide to long for ggplot
meltdata <- melt(inc2beta, id=c("temps"),
  variable.name = "level", 
  value.name = "respnorm")
#plot
p_inc <- ggplot() +
  geom_line(data=meltdata, aes(x=temps, y=respnorm, group=level), alpha = 0.2) +
  scale_colour_gradientn(colours=rainbow(3)) +
  theme_bw() +
  theme(panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(), 
        axis.line = element_line(colour = "black")) +
  xlab("Temperature") + ylab("Change in mins worked relative to 27C") +
  coord_cartesian(ylim = c(-100, 100), xlim =c(0,44))  +
  ggtitle("2 Factor Interaction (Income, Income^2, Degree Days) (Global, state x MOS FEs)")
ggsave(p_inc, file="Trin_test/2factor_2_full_inc2_beta.png")

colour=level, 

#png('Trin_test/2factor_2_full_inc2_beta.png')
#plot(temps,mid.respnorm, col = "chocolate1", type = "l", lwd = 3, xlim=c(0, 44), ylim=c(-100, 100),xlab="Temperature",ylab="Change in mins worked relative to 27C")
#lines(temps,hi.respnorm, col = "darkred", lwd = 2)
#lines(temps,lo.respnorm, col = "darkgoldenrod1", lwd = 2)
#mtext("2 Factor Interaction (Income, Income^2) (Full Sample, state x MOS FEs)", side = 3, line = 1)
#legend('topright', c("high: $17308","mid: $8378","low: $3606"), # puts text in the legend
       #lty=c(1,1,1), # gives the legend appropriate symbols (lines)
       #lwd=c(2,2,2),col=c("darkred","chocolate1","darkgoldenrod1")) # gives the legend lines the correct color and width
#dev.off()

#############################


#############################
#for hotdd_30
############################

#extract regression coefficients
cf <- summary(twofactors.two.full.dd.thirty.ten)$coef

#unnormalized response vector
resp <- cf['hotdd_30:tempL0_27nabove',1]*temps_hotdd_30 + cf['hotdd_30:temp2L0_27nabove',1]*temps_hotdd_30^2 + cf['hotdd_30:temp3L0_27nabove',1]*temps_hotdd_30^3 + cf['hotdd_30:temp4L0_27nabove',1]*temps_hotdd_30^4

#response at 27 C (vector)
resp27 <- cf['hotdd_30:tempL0_27nabove',1]*temp27_dd + cf['hotdd_30:temp2L0_27nabove',1]*temp27_dd^2 + cf['hotdd_30:temp3L0_27nabove',1]*temp27_dd^3 + cf['hotdd_30:temp4L0_27nabove',1]*temp27_dd^4

#normalized response vector
respnorm <- resp - resp27

#calculate se for each temperature and put it in a vector
#create se vector
se <- 0
#loop over each temp from -18 to -1
for (z in 1:18) {
  se[z] <- deltamethod(~ x14*(0-27) + x15*(0-27^2) + x16*(0-27^3) + x17*(0-27^4), coef(twofactors.two.full.dd.thirty.ten), vcov(twofactors.two.full.dd.thirty.ten))
} 

#loop over each temp from 30 to 44
for (z in 19:63) {
  se[z] <- deltamethod(~ x14*((z-19)-27) + x15*((z-19)^2-27^2) + x16*((z-19)^3-27^3) + x17*((z-19)^4-27^4), coef(twofactors.two.full.dd.thirty.ten), vcov(twofactors.two.full.dd.thirty.ten))
}
#view se vector
print(se)

#draw 0 line for plotting
for (m in 1:45) {
  respnorm[m] <-0
}

for (m in 1:45) {
  se[m] <-0
}

#confidence intervals
lowerci = respnorm - (1.96*se)
upperci = respnorm + (1.96*se)

#plot
resp.df <- data.frame(temps, temps_hotdd_30, respnorm, lowerci, upperci)
p <- ggplot() + geom_line(data=resp.df, aes(x=temps, y=respnorm), colour = "palegreen4") + 
  geom_ribbon(aes(ymin=resp.df$lowerci, ymax=resp.df$upperci, x=temps_hotdd_30), fill = "palegreen3", linetype=2, alpha=0.3) +
  theme_bw() +
  theme(panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(), 
        axis.line = element_line(colour = "black")) +
  xlab("Temperature") + ylab("Change in mins worked relative to 27C") +
  coord_cartesian(ylim = c(-0.1, 0.1), xlim =c(0,44))  +
  ggtitle("2 Factor Interaction (Hot Degree Days) (Full Sample, state x MOS FEs)")
ggsave(p, file="Trin_test/2factor_2_full_inc2_hotdd_30.png")


#############################
#for colddd_10
############################

#extract regression coefficients
cf <- summary(twofactors.two.full.dd.thirty.ten)$coef

#unnormalized response vector
resp <- cf['colddd_10:tempL0_below27',1]*temps_colddd_10 + cf['colddd_10:temp2L0_below27',1]*temps_colddd_10^2 + cf['colddd_10:temp3L0_below27',1]*temps_colddd_10^3 + cf['colddd_10:temp4L0_below27',1]*temps_colddd_10^4

#response at 27 C (vector)
temp27 <- rep(27,63)
resp27 <- cf['colddd_10:tempL0_below27',1]*temp27_cdd + cf['colddd_10:temp2L0_below27',1]*temp27_cdd^2 + cf['colddd_10:temp3L0_below27',1]*temp27_cdd^3 + cf['colddd_10:temp4L0_below27',1]*temp27_cdd^4

#normalized response vector
respnorm <- resp - resp27

#calculate se for each temperature and put it in a vector
#create se vector
se <- 0
#loop over each temp from -18 to -1
for (z in 1:18) {
  se[z] <- deltamethod(~ x18*(0-27) + x19*(0-(27^2)) + x20*(0-(27^3)) + x21*(0-(27^4)), coef(twofactors.two.full.dd.thirty.ten), vcov(twofactors.two.full.dd.thirty.ten))
} 

#loop over each temp from 0 to 44
for (z in 19:63) {
  se[z] <- deltamethod(~ x18*((z-19)-27) + x19*((z-19)^2-27^2) + x20*((z-19)^3-27^3) + x21*((z-19)^4-27^4), coef(twofactors.two.full.dd.thirty.ten), vcov(twofactors.two.full.dd.thirty.ten))
}
#view se vector
print(se)

#draw 0 line for plotting
for (m in 46:63) {
  respnorm[m] <-0
}

for (m in 46:63) {
  se[m] <-0
}

#confidence intervals
lowerci = respnorm - (1.96*se)
upperci = respnorm + (1.96*se)

#plot
resp.df <- data.frame(temps, temps_colddd_10, respnorm, lowerci, upperci)
p <- ggplot(data=resp.df, aes(x=temps, y=respnorm)) + geom_line(colour = "seashell4") + 
  geom_ribbon(aes(ymin=resp.df$lowerci, ymax=resp.df$upperci), fill = "seashell4", linetype=2, alpha=0.3) +
  theme_bw() +
  theme(panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(), 
        axis.line = element_line(colour = "black")) +
  coord_cartesian(ylim = c(-0.1, 0.1), xlim =c(0,44))  +
  xlab("Temperature") + ylab("Change in mins worked relative to 27C") +
  ggtitle("2 Factor Interaction (Cold Degree Days) (Full Sample, state x MOS FEs)")
ggsave(p, file="Trin_test/2factor_2_full_inc2_colddd_10.png")


