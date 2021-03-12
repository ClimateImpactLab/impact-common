"""
Various unit, smoke, and integration tests for impactcommon.exogenous_economy.gdppc
"""
import pytest
import numpy as np
import pandas as pd
from impactcommon.exogenous_economy import gdppc


@pytest.fixture
def support_dfs():
    """Setup, return simple unclean support baseline, growth, nightlight pd.DataFrame files, like those in shareddirs
    """
    baseline_df = pd.DataFrame(
        {
            "year": [2010, 2010, 2010],
            "model": ["low", "low", "low"],  # "iam"
            "scenario": ["SSP3", "SSP3", "SSP4"],  # "ssp"
            "iso": ["foo", "bar", "foo"],
            "value": np.arange(3, dtype=np.float64) + 1,
        }
    )
    growth_df = pd.DataFrame(
        {
            "year": [2015, 2010, 2015, 2020],
            "model": ["low", "low", "low", "high"],  # "iam"
            "scenario": ["SSP3", "SSP3", "SSP3", "SSP3"],  # "ssp"
            "iso": ["foo", "foo", "bar", "foo"],
            "growth": np.arange(4, dtype=np.float64) + 1,
        }
    )
    df_nightlights = pd.DataFrame(
        {
            "hierid": ["fooSPAM"],
            "gdppc_ratio": [2.0],
        }
    )
    return baseline_df, growth_df, df_nightlights


@pytest.fixture
def tmpsetup(tmpdir, support_dfs):
    """Setup uncleaned support CSV files in tmp directory for easy cleanup, without shareddir

    Returns
    -------
        Absolute paths to baseline, growth, and nightlights CSVs in tmp directory.
    """
    baseline_df, growth_df, df_nightlights = support_dfs

    gdppc_growth_path = tmpdir.join("gdppc-growth.csv")
    gdppc_baseline_path = tmpdir.join("gdppc-baseline.csv")
    nightlights_path = tmpdir.join("nightlights.csv")

    baseline_df.to_csv(gdppc_baseline_path, index=False)
    growth_df.to_csv(gdppc_growth_path, index=False)
    df_nightlights.to_csv(nightlights_path, index=False)
    return gdppc_baseline_path, gdppc_growth_path, nightlights_path


@pytest.fixture
def tmpsetup_shareddir(tmpdir, monkeypatch, support_dfs):
    """Setup shareddir with uncleaned files in tmp directory for cleanup

    The environment variable IMPERICS_SHAREDDIR is monkeypatched with shareddir
    path.

    Input files are kept in traditional shareddir paths: 'social/baselines/gdppc-growth.csv',
    'social/baselines/gdppc-merged-nohier.csv', 'social/baselines/nightlight_weight_normalized.csv'.
    """
    baseline_df, growth_df, df_nightlights = support_dfs

    shareddir = tmpdir.mkdir("shared")
    monkeypatch.setenv("IMPERICS_SHAREDDIR", str(shareddir))

    baseline_dir = shareddir.mkdir("social").mkdir("baselines")
    gdppc_growth_path = baseline_dir.join("gdppc-growth.csv")
    gdppc_baseline_path = baseline_dir.join("gdppc-merged-nohier.csv")
    nightlights_path = baseline_dir.join("nightlight_weight_normalized.csv")

    baseline_df.to_csv(gdppc_baseline_path, index=False)
    growth_df.to_csv(gdppc_growth_path, index=False)
    df_nightlights.to_csv(nightlights_path, index=False)


@pytest.mark.parametrize(
    "hierid, goal",
    [
        pytest.param(
            "fooSPAM",
            np.array([2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.]),
            id="hierid in nightlights",
        ),
        pytest.param(
            "fooEGGS",
            np.array([1.,  2.,  4.,  8., 16., 32., 32., 32., 32., 32., 32.]),
            id="hierid not in nightlights",
        ),
    ],
)
def test_hierarchicalgdppcprovider_get_timeseries(support_dfs, hierid, goal):
    """Simple test for HierarchicalGDPpcProvider.get_timeseries

    This test checks output for hierid with and without nightlights coverage.
    """
    baseline_df, growth_df, df_nightlights = support_dfs

    testprovider = gdppc.HierarchicalGDPpcProvider(
        iam="foo",
        ssp="SSP3",
        df_baseline=baseline_df,
        df_growth=growth_df,
        df_nightlights=df_nightlights,
        startyear=2010,
        stopyear=2020
    )
    actual = testprovider.get_timeseries(hierid=hierid)

    np.testing.assert_array_equal(actual, goal)


def test_hierarchicalgdppcprovider_get_iso_timeseries(support_dfs):
    """Simple test for HierarchicalGDPpcProvider.get_iso_timeseries"""
    baseline_df, growth_df, df_nightlights = support_dfs

    goal = np.array([1.,  2.,  4.,  8., 16., 32., 32., 32., 32., 32., 32.])

    testprovider = gdppc.HierarchicalGDPpcProvider(
        iam="foo",
        ssp="SSP3",
        df_baseline=baseline_df,
        df_growth=growth_df,
        df_nightlights=df_nightlights,
        startyear=2010,
        stopyear=2020
    )
    actual = testprovider.get_iso_timeseries(iso="foo")
    np.testing.assert_array_equal(actual, goal)


def test_read_hierarchicalgdppcprovider_shareddir(tmpsetup_shareddir):
    """
    Integration test for read_hierarchicalgdppcprovider with shareddirs

    Tests that files are read and cleaned from shareddir paths
    such that we get a timeseries from the provider, given a hierid.
    """
    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.read_hierarchicalgdppcprovider(
        iam=input_iam, ssp=input_ssp,
        growth_path_or_buffer='social/baselines/gdppc-growth.csv',
        baseline_path_or_buffer='social/baselines/gdppc-merged-nohier.csv',
        nightlights_path_or_buffer='social/baselines/nightlight_weight_normalized.csv',
        stopyear=2020, use_sharedpath=True
    )

    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)


def test_read_hierarchicalgdppcprovider_noshareddir(tmpsetup):
    """
    Integration test for read_hierarchicalgdppcprovider without using shareddirs

    Tests that files are read and cleaned from absolute paths
    such that we get a timeseries from the provider, given a hierid.
    """
    gdppc_baseline_path, gdppc_growth_path, nightlights_path = tmpsetup

    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.read_hierarchicalgdppcprovider(
        iam=input_iam,
        ssp=input_ssp,
        growth_path_or_buffer=str(gdppc_growth_path),
        baseline_path_or_buffer=str(gdppc_baseline_path),
        nightlights_path_or_buffer=str(nightlights_path),
        stopyear=2020
    )
    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)


def test_gdppcprovider(tmpsetup_shareddir):
    """
    Smoke and integration test for legacy GDPpcProvider behavior

    Specifically this is testing that files are read and cleaned from shareddir
    such that we get a timeseries from the provider, given a hierid.
    """
    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.GDPpcProvider(iam=input_iam, ssp=input_ssp, stopyear=2020)
    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)
