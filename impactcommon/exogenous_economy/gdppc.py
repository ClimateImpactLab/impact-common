from functools import lru_cache
from warnings import warn
import numpy as np
import pandas as pd
import metacsv
from impactlab_tools.utils import files
from . import provider


def read_bestgdppcprovider(iam, ssp, growth_path_or_buffer, baseline_path_or_buffer, nightlights_path_or_buffer,
                           startyear=2010, stopyear=2100, use_sharedpath=False):
    """
    Read files on disk to create a BestGDPpcProvider instance

    Parameters
    ----------
    iam : str
    ssp : str
    growth_path_or_buffer
        CSV file containing GDPpc growth projection at 5-year intervals. Must have columns giving "year",
        IAM model ("model"), SSP scenario ("scenario"), the ISO entity ("iso"),
        and the actual GDPpc growth values value ("growth").
    baseline_path_or_buffer
        CSV file containing GDPpc baseline values. Must have columns giving "year",
        IAM model ("model"), SSP scenario ("scenario"), the ISO entity ("iso"),
        and corresponding the actual GDPpc values ("value").
    nightlights_path_or_buffer
        CSV file of nightlight-based ratios for regions.
    startyear : int, optional
        Year to draw baseline value from. Must be in 'baseline_path_or_buffer' file's "year" column.
    stopyear : int, optional
        Must be within 5 years of the largest "year"  in 'growth_path_or_buffer'.
    use_sharedpath : bool, optional
        Interpret paths without leading "/" as "shareddir" paths?

    Returns
    -------
    out : BestGDPpcProvider

    Examples
    --------
    >>> provider = read_bestgdppcprovider(
    ...     'low', 'SSP3',
    ...     growth_path_or_buffer='inputdata/gdppc/growth.csv',
    ...     baseline_path_or_buffer='inputdata/gdppc/baseline.csv',
    ...     nightlights_path_or_buffer='inputdata/nightlights_normalized.csv'
    ... )
    >>> gdppcs = provider.get_timeseries('ZWE.2.2')  # Get the series for any hierid or ISO

    See Also
    --------
    BestGDPpcProvider : Provider of GDP per capita (GDPpc) timeseries, selecting "best" data source
    """
    if use_sharedpath:
        baseline_path_or_buffer = files.sharedpath(baseline_path_or_buffer)
        growth_path_or_buffer = files.sharedpath(growth_path_or_buffer)
        nightlights_path_or_buffer = files.sharedpath(nightlights_path_or_buffer)

    df = metacsv.read_csv(baseline_path_or_buffer)
    df_growth = metacsv.read_csv(files.sharedpath(growth_path_or_buffer))
    df_nightlights = metacsv.read_csv(files.sharedpath(nightlights_path_or_buffer))

    out = BestGDPpcProvider(
        iam=iam,
        ssp=ssp,
        df_baseline=df,
        df_growth=df_growth,
        df_nightlights=df_nightlights,
        startyear=startyear,
        stopyear=stopyear
    )
    return out


def GDPpcProvider(iam, ssp, baseline_year=2010, growth_filepath='social/baselines/gdppc-growth.csv',
                  baseline_filepath='social/baselines/gdppc-merged-nohier.csv',
                  nightlights_filepath='social/baselines/nightlight_weight_normalized.csv', stopyear=2100):
    """Get BestGDPpcProvider through the legacy GDPpcProvider interface

    This interface is deprecated, please use read_bestgdppcprovider() or
    instantiate BestGDPpcProvider, directly.

    Parameters
    ----------
    iam : str
    ssp : str
    baseline_year : int, optional
    growth_filepath : str, optional
    baseline_filepath : str, optional
    nightlights_filepath : str, optional
    stopyear : int, optional

    Returns
    -------
    out : impactcommmon.exogenous_economy.BestGDPpcProvider

    Examples
    --------
    >>> provider = GDPpcProvider('low', 'SSP3')  # Requires setting IMPERICS_SHAREDDIR.
    >>> gdppcs = provider.get_timeseries('ZWE.2.2')  # Get the series for any hierid or ISO

    See Also
    --------
    read_bestgdppcprovider : Read files on disk to create a BestGDPpcProvider instance
    BestGDPpcProvider : Provider of GDP per capita (GDPpc) timeseries, selecting "best" data source
    """
    warn(
        "GDPpcProvider is deprecated, please use read_bestgdppcprovider or BestGDPpcProvider, directly",
        DeprecationWarning
    )
    out = read_bestgdppcprovider(
        iam=iam,
        ssp=ssp,
        growth_path_or_buffer=growth_filepath,
        baseline_path_or_buffer=baseline_filepath,
        nightlights_path_or_buffer=nightlights_filepath,
        use_sharedpath=True,
        startyear=baseline_year,
        stopyear=stopyear
    )
    return out


class BestGDPpcProvider(provider.BySpaceProvider):
    """
    Provider of GDP per capita (GDPpc) timeseries, selecting "best" available source

    The provider selects the "best" data by using the highest priority data
    available: first data from the IAM, then from any IAM, then global.

    This is most commonly instantiated through ''read_bestgdppcprovider()''.

    Parameters
    ----------
    iam : str
        Target IAM model, e.g. "high" or "low".
    ssp : str
        Target SSP scenario, e.g. "SSP3".
    df_baseline : pd.Dataframe
        Annual GDPpc baseline observations. Must have columns giving "year",
        IAM model ("model"), SSP scenario ("scenario"), the ISO entity ("iso"),
        and corresponding the actual GDPpc value ("value").
    df_growth : pd.Dataframe
        Projected GDPpc differences at 5-year intervals. Must have the same
        columns as `df_baseline` ("year", "model", "scenario", "iso") but
        with a "growth" column of projected changes in GDPpc.
    df_nightlights : pd.Dataframe
    startyear : int, optional
        Year to draw baseline value from. Must be in 'df_baseline's "year" column.
    stopyear : int, optional
        Must be within 5 years of the largest "year"  in 'df_growth'.

    See Also
    --------
    read_bestgdppcprovider : Read files on disk to create a BestGDPpcProvider instance.
    """
    
    def __init__(self, iam, ssp, df_baseline, df_growth, df_nightlights, startyear=2010, stopyear=2100):
        """iam and ssp should be as described in the files (e.g., iam = 'low', ssp = 'SSP3')"""
        super().__init__(iam, ssp, startyear)
        self.stopyear = stopyear
        self.df_nightlights = df_nightlights

        # Need year index, but data has obs at 5-year intervals:
        df_growth['yearindex'] = np.int_((df_growth.year - self.startyear) / 5)

        self._populate_baseline_candidates(df_baseline)
        self._populate_growth_candidates(df_growth)

    def _populate_baseline_candidates(self, df):
        """Split-out baseline GDPpc so can choose priority data for regional timeseries"""
        match_year_ssp = (df.scenario == self.ssp) & (df.year == self.startyear)
        self.df_baseline_this = df.loc[(df.model == self.iam) & match_year_ssp]
        self.df_baseline_anyiam = df.loc[match_year_ssp].groupby('iso').median()
        self.baseline_global = df.loc[match_year_ssp].median()

    def _populate_growth_candidates(self, df):
        """Split-out GDPpc growth data so can choose priority data for regional timeseries"""
        self.df_growth_this = df.loc[(df.model == self.iam) & (df.scenario == self.ssp)]
        self.df_growth_anyiam = df.loc[(df.scenario == self.ssp)].groupby(['iso', 'year']).median()
        self.growth_global = df.loc[(df.scenario == self.ssp) & (df.model == self.iam)].groupby(['year']).median()

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

    def get_timeseries(self, hierid):
        """Return an np.array of GDPpc for the given region."""
        
        iso_gdppcs = self.get_iso_timeseries(hierid[:3])
        ratio = self.df_nightlights.loc[self.df_nightlights.hierid == hierid].gdppc_ratio
        if len(ratio) == 0:
            return iso_gdppcs # Assume all combined
        if np.isnan(ratio.values[0]) or ratio.values[0] == 0:
            return 0.8 * iso_gdppcs
        
        return iso_gdppcs * ratio.values[0]

    @lru_cache(maxsize=None)
    def get_iso_timeseries(self, iso):
        """Return an np.array of GDPpc for the given ISO country."""
        # Select baseline GDPpc
        df_baseline = self._get_best_iso_available(
            iso,
            self.df_baseline_this,
            self.df_baseline_anyiam,
            self.baseline_global
        )
        baseline = df_baseline.value
        if isinstance(baseline, pd.Series):
            baseline = baseline.values[0]

        # Select growth series
        df_growth = self._get_best_iso_available(
            iso,
            self.df_growth_this,
            self.df_growth_anyiam,
            self.growth_global
        )

        # Calculate GDPpc as they grow in time
        gdppcs = [baseline]
        for year in range(self.startyear + 1, self.stopyear + 1):
            yearindex = int((year - 1 - self.startyear) / 5) # Last year's growth
            growthrate = df_growth.loc[df_growth.yearindex == yearindex].growth.values
            new_gdppc = gdppcs[-1] * growthrate
            gdppcs.append(new_gdppc.item())

        return np.array(gdppcs)


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
