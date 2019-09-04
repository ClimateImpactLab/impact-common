import numpy as np
import pandas as pd
import metacsv
from impactlab_tools.utils import files
import provider

## Static configration
growth_filepath = 'social/baselines/gdppc-growth.csv'
baseline_filepath = 'social/baselines/gdppc-merged-nohier.csv'
nightlights_filepath = 'social/baselines/nightlight_weight_normalized.csv'
baseline_year = 2010

class GDPpcProvider(provider.BySpaceProvider):
    """
    GDPpcProvider returns timeseries of GDPpc for a given IAM and SSP.

    Usage example:
      provider = GDPpcProvider('low', 'SSP3') # initialize the provider
      gdppcs = provider.get_timeseries('ZWE.2.2') # get the series for any hierid or ISO
      provider.get_startyear() # the first year
    
    Testing it:
      1. Clone the impact-common repository to a folder.
      2. Make a server.yml file in the same directory with the contents "shareddir: <path to GCP data dir.>"
      3. cd into the impact-common directory and run:
           python -m impactcommon.exogenous_economy.gdppc
    """
    
    def __init__(self, iam, ssp):
        """iam and ssp should be as described in the files (e.g., iam = 'low', ssp = 'SSP3')"""

        super(GDPpcProvider, self).__init__(iam, ssp, baseline_year)

        # Load the baseline values, and split by priority of data
        df = metacsv.read_csv(files.sharedpath(baseline_filepath))
        self.df_baseline_this = df.loc[(df.model == iam) & (df.scenario == ssp) & (df.year == baseline_year)]
        self.df_baseline_anyiam = df.loc[(df.scenario == ssp) & (df.year == baseline_year)].groupby('iso').median()
        self.baseline_global = df.loc[(df.scenario == ssp) & (df.year == baseline_year)].median()

        # Load the growth rates, and split by priority of data
        df_growth = metacsv.read_csv(files.sharedpath(growth_filepath))
        df_growth['yearindex'] = np.int_((df_growth.year - baseline_year) / 5)
        self.df_growth_this = df_growth.loc[(df_growth.model == iam) & (df_growth.scenario == ssp)]
        self.df_growth_anyiam = df_growth.loc[(df_growth.scenario == ssp)].groupby(['iso', 'year']).median()
        self.growth_global = df_growth.loc[(df_growth.scenario == ssp) & (df_growth.model == iam)].groupby(['year']).median()

        # Load the nightlights
        self.df_nightlights = metacsv.read_csv(files.sharedpath(nightlights_filepath))

        # Cache for ISO-level GDPpc series
        self.cached_iso_gdppcs = {}
        
    def get_timeseries(self, hierid):
        """Return an np.array of GDPpc for the given region."""
        
        iso_gdppcs = self.get_iso_timeseries(hierid[:3])
        ratio = self.df_nightlights.loc[self.df_nightlights.hierid == hierid].gdppc_ratio
        if len(ratio) == 0:
            return iso_gdppcs # Assume all combined
        if np.isnan(ratio.values[0]) or ratio.values[0] == 0:
            return 0.8 * iso_gdppcs
        
        return iso_gdppcs * ratio.values[0]

    def get_iso_timeseries(self, iso):
        """Return an np.array of GDPpc for the given ISO country."""

        # Use the cache if available
        if iso not in self.cached_iso_gdppcs:
            # Select baseline GDPpc
            df_baseline = self._get_best_iso_available(iso, self.df_baseline_this,
                                                      self.df_baseline_anyiam,
                                                      self.baseline_global)
            baseline = df_baseline.value
            if isinstance(baseline, pd.Series):
                baseline = baseline.values[0]

            # Select growth series
            df_growth = self._get_best_iso_available(iso, self.df_growth_this,
                                                    self.df_growth_anyiam,
                                                    self.growth_global)

            # Calculate GDPpc as they grow in time
            gdppcs = [baseline]
            for year in range(baseline_year + 1, 2100 + 1):
                yearindex = int((year - 1 - baseline_year) / 5) # Last year's growth
                growthrate = df_growth.loc[df_growth.yearindex == yearindex].growth.values
                new_gdppcs = gdppcs[-1] * growthrate
                gdppcs.append(new_gdppcs.item())

            self.cached_iso_gdppcs[iso] = np.array(gdppcs)
            
        return self.cached_iso_gdppcs[iso]

    def _get_best_iso_available(self, iso, df_this, df_anyiam, df_global):
        """Get the highest priority data available: first data from the IAM, then from any IAM, then global."""
        
        df = df_this.loc[df_this.iso == iso]
        if df.shape[0] > 0:
            return df

        if iso in df_anyiam.index:
            df = df_anyiam.loc[iso]
            if df.shape[0] > 0:
                return df
        
        return df_global
    
if __name__ == '__main__':
    # Test the provider
    import time

    time0 = time.time()
    provider = GDPpcProvider('low', 'SSP3')
    df = metacsv.read_csv(files.sharedpath("regions/hierarchy_metacsv.csv"))
    time1 = time.time()
    print "Load time: %s seconds" % (time1 - time0)

    for ii in np.where(df.is_terminal)[0]:
        xx = provider.get_timeseries(df.iloc[ii, 0])
    time2 = time.time()
    print "First pass: %s seconds" % (time2 - time1)

    for ii in np.where(df.is_terminal)[0]:
        xx = provider.get_timeseries(df.iloc[ii, 0])
    time3 = time.time()
    print "Second pass: %s seconds" % (time3 - time2)
