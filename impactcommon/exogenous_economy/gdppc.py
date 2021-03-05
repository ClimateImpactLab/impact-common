from warnings import warn
import numpy as np
import pandas as pd
import metacsv
from impactlab_tools.utils import files
from . import provider


def read_gdpprovider(iam, ssp, growth_path_or_buffer, baseline_path_or_buffer, nightlights_path_or_buffer,
                     baseline_year=2010, sharedpath=False):
    if sharedpath:
        baseline_path_or_buffer = files.sharedpath(baseline_path_or_buffer)
        growth_path_or_buffer = files.sharedpath(growth_path_or_buffer)
        nightlights_path_or_buffer = files.sharedpath(nightlights_path_or_buffer)

    df = metacsv.read_csv(baseline_path_or_buffer)
    df_growth = metacsv.read_csv(files.sharedpath(growth_path_or_buffer))
    df_nightlights = metacsv.read_csv(files.sharedpath(nightlights_path_or_buffer))

    # Need year index, but data has obs at 5-year intervals:
    df_growth['yearindex'] = np.int_((df_growth.year - baseline_year) / 5)

    out = GdpProvider(iam=iam, ssp=ssp, baseline_df=df, growth_df=df_growth, df_nightlights=df_nightlights,
                      startyear=2010)
    return out


def GDPpcProvider(iam, ssp, baseline_year=2010, growth_filepath='social/baselines/gdppc-growth.csv',
                  baseline_filepath='social/baselines/gdppc-merged-nohier.csv',
                  nightlights_filepath='social/baselines/nightlight_weight_normalized.csv', sharedpath=True):
    warn("GDPpcProvider is deprecated, please use read_gdpprovider or GdpProvider, directly", DeprecationWarning)
    out = read_gdpprovider(iam=iam, ssp=ssp, growth_path_or_buffer=growth_filepath,
                           baseline_path_or_buffer=baseline_filepath, nightlights_path_or_buffer=nightlights_filepath,
                           baseline_year=baseline_year, sharedpath=sharedpath)
    return out


def _split_baseline(df, iam, ssp, baseline_year):
    """Split-out baseline GDPpc so can choose priority data for regional timeseries"""
    this_df = df.loc[(df.model == iam) & (df.scenario == ssp) & (df.year == baseline_year)]
    anyiam_df = df.loc[(df.scenario == ssp) & (df.year == baseline_year)].groupby('iso').median()
    global_df = df.loc[(df.scenario == ssp) & (df.year == baseline_year)].median()
    return this_df, anyiam_df, global_df


def _split_growth(df, iam, ssp):
    """Split-out GDPpc growth data so can choose priority data for regional timeseries"""
    this_df = df.loc[(df.model == iam) & (df.scenario == ssp)]
    anyiam_df = df.loc[(df.scenario == ssp)].groupby(['iso', 'year']).median()
    global_df = df.loc[(df.scenario == ssp) & (df.model == iam)].groupby(['year']).median()
    return this_df, anyiam_df, global_df


class GdpProvider(provider.BySpaceProvider):
    """
    Provider for timeseries of Gross domestic product per capita (GDPpc) for a given IAM and SSP.

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
    
    def __init__(self, iam, ssp, baseline_df, growth_df, df_nightlights, startyear=2010):
        """iam and ssp should be as described in the files (e.g., iam = 'low', ssp = 'SSP3')"""
        super().__init__(iam, ssp, startyear)
        self.df_nightlights = df_nightlights

        # Split growth and baseline data by data priority
        self.df_baseline_this, self.df_baseline_anyiam, self.baseline_global = _split_baseline(baseline_df,
                                                                                               self.iam, self.ssp,
                                                                                               self.startyear)
        self.df_growth_this, self.df_growth_anyiam, self.growth_global = _split_growth(growth_df, self.iam, self.ssp)

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
            for year in range(self.startyear + 1, 2100 + 1):
                yearindex = int((year - 1 - self.startyear) / 5) # Last year's growth
                growthrate = df_growth.loc[df_growth.yearindex == yearindex].growth.values
                new_gdppc = gdppcs[-1] * growthrate
                gdppcs.append(new_gdppc.item())

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
    print("Load time: %s seconds" % (time1 - time0))

    for ii in np.where(df.is_terminal)[0]:
        xx = provider.get_timeseries(df.iloc[ii, 0])
    time2 = time.time()
    print("First pass: %s seconds" % (time2 - time1))

    for ii in np.where(df.is_terminal)[0]:
        xx = provider.get_timeseries(df.iloc[ii, 0])
    time3 = time.time()
    print("Second pass: %s seconds" % (time3 - time2))
