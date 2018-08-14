import numpy as np
import pandas as pd
import metacsv
import provider

growth_filepath = 'social/baselines/gdppc-growth.csv'
baseline_filepath = 'social/baselines/gdppc-merged-nohier.csv'
nightlights_filepath = 'social/baselines/nightlight_weight.csv'
baseline_year = 2010

class GDPpcProvider(Provider):
    def __init__(self, iam, ssp):
        super(GDPpcProvider, self).__init__(iam, ssp, baseline_year)

        df = metacsv.read_csv(files.sharedpath(baseline_filepath))
        self.df_baseline_this = df.loc[(df.model == iam) & (df.scenario == ssp) & (df.year == baseline_year)]
        self.df_baseline_anyiam = df.loc[(df.scenario == ssp) & (df.year == baseline_year)].groupby('iso').median()
        self.baseline_global = df.loc[(df.scenario == ssp) & (df.year == baseline_year)].median()
        
        df_growth = metacsv.read_csv(files.sharedpath(growth_filepath))
        df_growth['yearindex'] = np.int_((df_growth.year - baseline_year) / 5)
        self.df_growth_this = df_growth.loc[(df_growth.model == iam) & (df_growth.scenario == ssp)]
        self.df_growth_anyiam = df_growth.loc[(df_growth.scenario == ssp)].groupby(['iso', 'year']).median()
        self.growth_global = df_growth.loc[(df_growth.scenario == ssp) & (df_growth.iso == 'mean')]
        
        self.df_nightlights = metacsv.read_csv(files.sharedpath(nightlights_filepath))

        self.cached_iso_gdppcs = {}
        
    def get_timeseries(self, hierid):
        iso_gdppcs = get_iso_timeseries(hierid[:3])
        ratio = df_nightlights.loc[df_nightlights.hierid == hierid].gdppc_ratio
        return iso_gdppcs * ratio

    def get_iso_timeseries(self, iso):
        if iso not in self.cached_iso_gdppcs:
            # Select baseline GDPpc
            df_baseline = self.get_best_iso_available(iso, self.df_baseline_this,
                                                      self.df_baseline_anyiam,
                                                      self.baseline_global)
            baseline = df_baseline.value

            # Select growth series
            df_growth = self.get_best_iso_available(iso, self.df_growth_this,
                                                    self.df_growth_anyiam,
                                                    self.growth_global)

            gdppcs = [baseline]
            for year in range(baseline_year + 1, 2100 + 1):
                yearindex = int((year - 1 - baseline) / 5) # Last year's growth
                growthrate = df_growth.loc[df_growth.yearindex == yearindex].growth
                gdppcs.append(gdppcs[-1] * growthrate)

            self.cached_iso_gdppcs[iso] = np.array(gdppcs)
            
        return self.cached_iso_gdppcs[iso]

    def get_best_iso_available(self, iso, df_this, df_anyiam, df_global):
        df = self.df_this.loc[self.df_this.iso == iso]
        if df.shape[0] > 0:
            return df

        df = self.df_anyiam.loc[self.df_any.iso == iso]
        if df.shape[0] > 0:
            return df
        
        return df_global

if __name__ == '__main__':
    provider = GDPpcProvider('low', 'SSP3')
    print provider.get_timeseries('ZWE.2.2')
    print provider.get_timeseries('ABW')
