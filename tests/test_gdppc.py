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
            "model": [ "low", "low", "low"],  # "iam"
            "scenario": [ "SSP3", "SSP3", "SSP4"],  # "ssp"
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
    df_nightlights=pd.DataFrame(
        {
            "hierid" : ["fooSPAM"],
            "gdppc_ratio" : [2.0],
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


def test_split_baseline():
    """Basic smoke test that _split_baseline subsets correctly"""
    in_df = pd.DataFrame(
        {
            "year": [2010, 2010, 2005, 2010, 2010, 2005],
            "model": ["low", "low", "low", "low", "high", "high"],  # "iam"
            "scenario": ["SSP4", "SSP3", "SSP3", "SSP3", "SSP3", "SSP3"],  # "ssp"
            "iso": ["foo"] * 3 + ["bar"] * 3,
            "value": np.arange(6, dtype=np.float64),
        }
    )

    # Directly selecting this goal to avoid making a special index from scratch.
    this_goal = in_df.iloc[[1, 3]].copy()
    anyiam_goal = pd.DataFrame(
        {
            "year": [2010, 2010],
            "iso": ["bar", "foo"],
            "value": np.array([3.5, 1.0], dtype=np.float64),
        }
    )
    anyiam_goal = anyiam_goal.set_index("iso")
    globe_goal = pd.Series({"year": 2010.0, "value": 3.0})

    this, anyiam, globe = gdppc._split_baseline(
        in_df, iam="low", ssp="SSP3", baseline_year=2010
    )

    pd.testing.assert_frame_equal(this, this_goal)
    pd.testing.assert_frame_equal(anyiam, anyiam_goal)
    pd.testing.assert_series_equal(globe, globe_goal)


def test_split_growth():
    """Basic smoke test that _split_baseline subsets correctly"""
    in_df = pd.DataFrame(
        {
            "year": [2010, 2010, 2005, 2010, 2010, 2005],
            "model": ["low", "low", "low", "low", "high", "high"],  # "iam"
            "scenario": ["SSP4", "SSP3", "SSP3", "SSP3", "SSP3", "SSP3"],  # "ssp"
            "iso": ["foo"] * 3 + ["bar"] * 3,
            "growth": np.arange(6, dtype=np.float64),
        }
    )

    # Directly selecting this one to avoid making a special index from scratch:
    this_goal = in_df.iloc[[1, 2, 3]].copy()
    anyiam_goal = pd.DataFrame(
        {
            "year": [2005, 2010, 2005, 2010],
            "iso": ["bar", "bar", "foo", "foo"],
            "growth": np.array([5.0, 3.5, 2.0, 1.0], dtype=np.float64),
        }
    ).set_index(["iso", "year"])
    globe_goal = pd.DataFrame(
        {"year": [2005, 2010], "growth": [2.0, 2.0]}
    ).set_index("year")

    this, anyiam, globe = gdppc._split_growth(in_df, iam="low", ssp="SSP3")

    pd.testing.assert_frame_equal(this, this_goal)
    pd.testing.assert_frame_equal(anyiam, anyiam_goal)
    pd.testing.assert_frame_equal(globe, globe_goal)


def test_get_best_iso_available():
    """Test that _get_best_iso_available() correctly selects "best" data.

    This tests 4 specific selection cases.
    """
    # Setup inputs.
    df_this = pd.DataFrame(
        {
            "year": [2005, 2010],
            "model": ["low", "high"],  # "iam"
            "scenario": ["SSP3", "SSP3"],  # "ssp"
            "iso": ["foo", "spam"],
            "growth": np.array([2, 3], dtype=np.float64),
        }
    )
    df_anyiam = pd.DataFrame(
        {
            "year": [2005, 2010],
            "iso": ["foo", "bar"],
            "growth": np.array([2, 3], dtype=np.float64),
        }
    ).set_index(["iso", "year"])
    df_global = pd.DataFrame({"year": [2005, 2010], "growth": [2.0, 2.0]}).set_index("year")

    # Setup goals
    foo_goal = df_this.iloc[[0]].copy()
    spam_goal = df_this.iloc[[1]].copy()
    bar_goal = df_anyiam.loc["bar"].copy()
    zoo_goal = df_global.copy()

    foo_actual = gdppc._get_best_iso_available(
        iso="foo",
        df_this=df_this,
        df_anyiam=df_anyiam,
        df_global=df_global
    )
    spam_actual = gdppc._get_best_iso_available(
        iso="spam",
        df_this=df_this,
        df_anyiam=df_anyiam,
        df_global=df_global
    )
    bar_actual = gdppc._get_best_iso_available(
        iso="bar",
        df_this=df_this,
        df_anyiam=df_anyiam,
        df_global=df_global
    )
    zoo_actual = gdppc._get_best_iso_available(
        iso="zoo",
        df_this=df_this,
        df_anyiam=df_anyiam,
        df_global=df_global
    )

    pd.testing.assert_frame_equal(foo_actual, foo_goal)
    pd.testing.assert_frame_equal(spam_actual, spam_goal)
    pd.testing.assert_frame_equal(bar_actual, bar_goal)
    pd.testing.assert_frame_equal(zoo_actual, zoo_goal)


@pytest.mark.parametrize(
    "hierid, goal",
    [
        pytest.param(
            "fooSPAM",
            np.array([ 2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.]),
            id="hierid in nightlights",
        ),
        pytest.param(
            "fooEGGS",
            np.array([ 1.,  2.,  4.,  8., 16., 32., 32., 32., 32., 32., 32.]),
            id="hierid not in nightlights",
        ),
    ],
)
def test_bestgdppcprovider_get_timeseries(support_dfs, hierid, goal):
    """Simple test for BestGDPpcProvider.get_timeseries

    This test checks output for hierid with and without nightlights coverage.
    """
    baseline_df, growth_df, df_nightlights = support_dfs

    testprovider = gdppc.BestGDPpcProvider(
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


def test_bestgdppcprovider_get_iso_timeseries(support_dfs):
    """Simple test for BestGDPpcProvider.get_iso_timeseries"""
    baseline_df, growth_df, df_nightlights = support_dfs

    goal = np.array([ 1.,  2.,  4.,  8., 16., 32., 32., 32., 32., 32., 32.])

    testprovider = gdppc.BestGDPpcProvider(
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


def test_read_bestgdppcprovider_shareddir(tmpsetup_shareddir):
    """
    Integration test for read_bestgdppcprovider with shareddirs

    Tests that files are read and cleaned from shareddir paths
    such that we get a timeseries from the provider, given a hierid.
    """
    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([ 2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.read_bestgdppcprovider(
        iam=input_iam, ssp=input_ssp,
        growth_path_or_buffer='social/baselines/gdppc-growth.csv',
        baseline_path_or_buffer='social/baselines/gdppc-merged-nohier.csv',
        nightlights_path_or_buffer='social/baselines/nightlight_weight_normalized.csv',
        stopyear=2020, use_sharedpath=True
    )

    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)


def test_read_bestgdppcprovider_noshareddir(tmpsetup):
    """
    Integration test for read_bestgdppcprovider without using shareddirs

    Tests that files are read and cleaned from absolute paths
    such that we get a timeseries from the provider, given a hierid.
    """
    gdppc_baseline_path, gdppc_growth_path, nightlights_path = tmpsetup

    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([ 2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.read_bestgdppcprovider(
        iam=input_iam,
        ssp=input_ssp,
        growth_path_or_buffer=str(gdppc_growth_path),
        baseline_path_or_buffer=str(gdppc_baseline_path),
        nightlights_path_or_buffer=str(nightlights_path),
        stopyear=2020
    )
    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)


def test_GDPpcProvider(tmpsetup_shareddir):
    """
    Smoke and integration test for legacy GDPpcProvider behavior

    Specifically this is testing that files are read and cleaned from shareddir
    such that we get a timeseries from the provider, given a hierid.
    """
    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([ 2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.GDPpcProvider(iam=input_iam, ssp=input_ssp, stopyear=2020)
    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)
