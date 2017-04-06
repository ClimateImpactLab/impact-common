/*
Creator: Greg Dobbels, gdobbels@uchicago.edu
Date last modified: 
Last modified by: First Last, my@email.com
Purpose: 
Files used: 
Files created: 

Do Notes:

La Porta income data has adm1 level available for a subset panel years. 
	This code linearly interpolates income figures between available panel
	years and use the last (or first) available panel year to constantly
	extrapolate beyond income data availability.
*/

*************************************************************************
* 							PART A. Initializing						*			
*************************************************************************
	clear all		
	set more off
	pause on
	cap set processors 6

*************************************************************************
* 		PART A. Prep World Bank WDI Income Data for Merge with Yield Data		*			
*************************************************************************	

/*import
import delimited "$dir/6_covariates/2_income/WorldBank_WDI_income_2013.csv", stringcols(_all) clear

	*housekeeping
	rename ïcountry adm0
	rename date year
	rename value gdppc_adm0_wb
	destring year, replace
	replace adm0 = subinstr(lower(adm0)," ","_",.)
	keep adm0 year gdppc_adm0_wb
	
	replace adm0 = "macedonia" if adm0 == "macedonia,_fyr"
	replace adm0 = "venezuela" if adm0 == "venezuela,_rb"
*/	
import excel "C:\Users\Greg Dobbels\Desktop\VDATA.xlsx", clear firstrow allstring case(lower)

keep if ind1_desc == "GDP, PPP (constant 2005 international $)" ///
	| ind1_desc == "GDP per capita, PPP (constant 2005 international $)" ///
	| ind1_desc == "Population, total"
	
drop ind1
	
replace ind1_desc = "pop" if ind1_desc == "Population, total"
replace ind1_desc = "gdp" if ind1_desc == "GDP, PPP (constant 2005 international $)"
replace ind1_desc = "gdppc" if ind1_desc == "GDP per capita, PPP (constant 2005 international $)"

reshape long yr, i(country ind1_desc) j(year) string
reshape wide yr, i(country year) j(ind1_desc) string

foreach var in pop gdp gdppc {
	rename yr`var' `var'
	destring `var', replace
}

rename country_name adm0
replace adm0 = subinstr(lower(adm0)," ","_",.)

	replace adm0 = "macedonia" if adm0 == "macedonia,_fyr"
	replace adm0 = "venezuela" if adm0 == "venezuela,_rb"

destring year, replace

rename gdppc gdppc_adm0_wb

drop country
	
tempfile worldbank
save "`worldbank'"
	
*************************************************************************
* 		PART A. Prep La Porta Income Data for Merge with Yield Data		*			
*************************************************************************

*import
import delimited "$dir/6_covariates/2_income/Gennaioli2014_full.csv", stringcols(_all) clear

	*housekeeping
	rename country adm0
	rename code iso
	rename region adm1
	rename gdppccountry gdppc_adm0
	rename gdppcstate gdppc_adm1
	keep iso adm0 adm1 gdppc* year
	destring year, replace
	replace adm0 = subinstr(lower(adm0)," ","_",.)
	replace adm1 = subinstr(lower(adm1)," ","_",.)

	
*interpolate adm0 income measures
//preserve

	*collapse to adm0
	drop adm1 gdppc_adm1 
	duplicates drop
	
	merge 1:1 adm0 year using "`worldbank'"
	
	destring gdppc_adm0, replace
	gen dif_share = (gdppc_adm0_wb - gdppc_adm0) / gdppc_adm0
	
	qui count if !mi(dif_share)
	histogram dif_share, ///
		frequency title("Percent Difference between La Porta & WDI gdppc", ///
		color(black) margin(zero) size(small)) ///
		subtitle("(WDI - La Porta) / La Porta", color(black) margin(zero) size(small)) ///
		note("(`r(N)' total observations)", color(black) margin(zero) size(vsmall)) ///
		graphregion(color(white)) fcolor(bluishgray) lcolor(dknavy) ///
		xtitle("percent difference") ytitle("number of observations") bin(75)
	graph export "C:/Users/Greg Dobbels/Desktop/income_dif.png", replace
/*

	*create empty rows to build a complete year set for the panel
	sort adm0 year
	by adm0: gen post_years = year[_n+1] - year
	expand post_years, gen(new_obs)
	
	*update observation years
	bysort adm0 year new_obs: gen pos = _n
	replace year = year + pos if new_obs
	
	*drop gdppc for new observations, convert to numeric, and interpolate while we're at it
	foreach var of varlist gdppc* {
		destring `var', replace
		replace `var' = . if new_obs
		bysort adm0: ipolate `var' year, gen(new_`var')
		replace `var' = new_`var' if mi(`var')
		drop new_`var'
	}
	drop post_years new_obs pos
		
	*generate observations past last availabe year of income data
	bysort adm0: egen last_year = max(year)
	gen post_years = 2015 - year + 1 if last_year == year
	expand post_years, gen(new_obs)
	bysort adm0 year new_obs: gen pos = _n
	replace year = year + pos if new_obs
	drop post_years new_obs pos last_year
	
	*generate observations prior to first available year of income data
	bysort adm0: egen first_year = min(year)
	gen pre_years = year - 1950 if first_year == year
	expand pre_years, gen(new_obs)
	bysort adm0 year new_obs: gen pos = _n
	replace year = year - pos if new_obs
	drop pre_years new_obs pos first_year

	*save for merge w/ all yield data
	compress
	save "$dir/6_covariates/2_income/Gennaioli2014_full_interpolated_adm0.dta", replace

restore
	
*interpolate adm1 data (seperate process due to unbalanced panels within countries)	

	drop gdppc_adm0
	
	*create empty rows to build a complete year set for the panel
	sort adm0 adm1 year
	by adm0 adm1: gen post_years = year[_n+1] - year
	expand post_years, gen(new_obs)
	
	*update observation years
	bysort adm0 adm1 year new_obs: gen pos = _n
	replace year = year + pos if new_obs
	
	*drop gdppc for new observations, convert to numeric, and interpolate while we're at it
	foreach var of varlist gdppc* {
		destring `var', replace
		replace `var' = . if new_obs
		bysort adm0 adm1: ipolate `var' year, gen(new_`var')
		replace `var' = new_`var' if mi(`var')
		drop new_`var'
	}
	drop post_years new_obs pos
		
	*generate observations past last availabe year of income data
	bysort adm0 adm1: egen last_year = max(year)
	gen post_years = 2015 - year + 1 if last_year == year
	expand post_years, gen(new_obs)
	bysort adm0 adm1 year new_obs: gen pos = _n
	replace year = year + pos if new_obs
	drop post_years new_obs pos last_year
	
	*generate observations prior to first available year of income data
	bysort adm0 adm1: egen first_year = min(year)
	gen pre_years = year - 1950 if first_year == year
	expand pre_years, gen(new_obs)
	bysort adm0 adm1 year new_obs: gen pos = _n
	replace year = year - pos if new_obs
	drop pre_years new_obs pos first_year
	
*save output
compress
export delimited "$dir/6_covariates/2_income/Gennaioli2014_full_interpolated.csv", replace

	
