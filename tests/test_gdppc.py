from unittest.mock import patch
import numpy as np
import pandas as pd
from impactcommon.exogenous_economy import gdppc


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
    globe_goal = pd.DataFrame({"year": [2005, 2010], "growth": [2.0, 2.0]}).set_index("year")

    this, anyiam, globe = gdppc._split_growth(in_df, iam="low", ssp="SSP3")

    pd.testing.assert_frame_equal(this, this_goal)
    pd.testing.assert_frame_equal(anyiam, anyiam_goal)
    pd.testing.assert_frame_equal(globe, globe_goal)


def test_get_best_iso_available():
    """Test that _get_best_iso_available() correctly selects "best" data.

    This tests 4 specific selection cases.
    """
    # TODO: This test should be refactored into a parameterized test, or broken into separate tests.

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


def test_GdpProvider_get_timeseries():
    """Simple test for GdpProvider.get_timeseries

    This test checks output for hierid with and without nightlights coverage.
    """
    # TODO: This test should be refactored into a parameterized test, or broken into separate tests.
    goal_foospam = np.array([ 2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    goal_fooeggs = np.array([ 1.,  2.,  4.,  8., 16., 32., 32., 32., 32., 32., 32.])

    testprovider = gdppc.GdpProvider(
        iam="foo",
        ssp="SSP3",
        baseline_df = pd.DataFrame(
            {
                "year": [2005, 2005],
                "model": [ "low", "low"],  # "iam"
                "scenario": [ "SSP3", "SSP3"],  # "ssp"
                "iso": ["foo", "bar"],
                "value": np.arange(2, dtype=np.float64) + 1,
            }
        ),
        growth_df = pd.DataFrame(
            {
                "year": [2010, 2005, 2010],
                "yearindex": [1, 0, 1],
                "model": ["low", "low", "low"],  # "iam"
                "scenario": ["SSP3", "SSP3", "SSP3"],  # "ssp"
                "iso": ["foo", "foo", "bar"],
                "growth": np.arange(3, dtype=np.float64) + 1,
            }
        ),
        df_nightlights=pd.DataFrame(
            {
                "hierid" : ["fooSPAM"],
                "gdppc_ratio" : [2.0],
            }
        ),
        startyear=2005,
        stopyear=2015
    )
    actual_foospam = testprovider.get_timeseries(hierid="fooSPAM")
    # Test case for hierid not being in nightlights.
    actual_fooeggs = testprovider.get_timeseries(hierid="fooEGGS")

    np.testing.assert_array_equal(actual_foospam, goal_foospam)
    np.testing.assert_array_equal(actual_fooeggs, goal_fooeggs)


def test_GdpProvider_get_iso_timeseries():
    """Simple test for GdpProvider.get_iso_timeseries"""
    goal = np.array([ 1.,  2.,  4.,  8., 16., 32., 32., 32., 32., 32., 32.])

    testprovider = gdppc.GdpProvider(
        iam="foo",
        ssp="SSP3",
        baseline_df = pd.DataFrame(
            {
                "year": [2005, 2005],
                "model": [ "low", "low"],  # "iam"
                "scenario": [ "SSP3", "SSP3"],  # "ssp"
                "iso": ["foo", "bar"],
                "value": np.arange(2, dtype=np.float64) + 1,
            }
        ),
        growth_df = pd.DataFrame(
            {
                "year": [2010, 2005, 2010],
                "yearindex": [1, 0, 1],
                "model": ["low", "low", "low"],  # "iam"
                "scenario": ["SSP3", "SSP3", "SSP3"],  # "ssp"
                "iso": ["foo", "foo", "bar"],
                "growth": np.arange(3, dtype=np.float64) + 1,
            }
        ),
        df_nightlights=pd.DataFrame(
            {
                "hierid" : ["fooSPAM"],
                "gdppc_ratio" : [2.0],
            }
        ),
        startyear=2005,
        stopyear=2015
    )
    actual = testprovider.get_iso_timeseries(iso="foo")
    np.testing.assert_array_equal(actual, goal)


def test_read_gdpprovider_shareddir(monkeypatch, tmpdir):
    """
    Integration test for read_gdpprovider with shareddirs

    Tests that files are read and cleaned from shareddir paths
    such that we get a timeseries from the provider, given a hierid.
    """
    shareddir = tmpdir.mkdir("shared")
    monkeypatch.setenv("IMPERICS_SHAREDDIR", str(shareddir))

    baseline_dir = shareddir.mkdir("social").mkdir("baselines")
    gdppc_growth_path = baseline_dir.join("gdppc-growth.csv")
    gdppc_baseline_path = baseline_dir.join("gdppc-merged-nohier.csv")
    nightlights_path = baseline_dir.join("nightlight_weight_normalized.csv")

    # Data to dump to temp files.
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

    baseline_df.to_csv(gdppc_baseline_path, index=False)
    growth_df.to_csv(gdppc_growth_path, index=False)
    df_nightlights.to_csv(nightlights_path, index=False)

    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([ 2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.read_gdpprovider(iam=input_iam, ssp=input_ssp,
                                          growth_path_or_buffer=gdppc_growth_path,
                                          baseline_path_or_buffer=gdppc_baseline_path,
                                          nightlights_path_or_buffer=nightlights_path,
                                          stopyear=2020, use_sharedpath=True)

    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)


def test_read_gdpprovider_noshareddir(tmpdir):
    """
    Integration test for read_gdpprovider without using shareddirs

    Tests that files are read and cleaned from absolute paths
    such that we get a timeseries from the provider, given a hierid.
    """
    gdppc_growth_path = tmpdir.join("gdppc-growth.csv")
    gdppc_baseline_path = tmpdir.join("gdppc-baseline.csv")
    nightlights_path = tmpdir.join("nightlights.csv")

    # Data to dump to temp files.
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

    baseline_df.to_csv(gdppc_baseline_path, index=False)
    growth_df.to_csv(gdppc_growth_path, index=False)
    df_nightlights.to_csv(nightlights_path, index=False)

    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([ 2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.read_gdpprovider(iam=input_iam, ssp=input_ssp,
                                          growth_path_or_buffer=str(gdppc_growth_path),
                                          baseline_path_or_buffer=str(gdppc_baseline_path),
                                          nightlights_path_or_buffer=str(nightlights_path),
                                          stopyear=2020)
    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)


def test_GDPpcProvider(monkeypatch, tmpdir):
    """
    Smoke and integration test for legacy GDPpcProvider behavior

    Specifically this is testing that files are read and cleaned from shareddir
    such that we get a timeseries from the provider, given a hierid.
    """
    shareddir = tmpdir.mkdir("shared")
    monkeypatch.setenv("IMPERICS_SHAREDDIR", str(shareddir))

    baseline_dir = shareddir.mkdir("social").mkdir("baselines")
    gdppc_growth_path = baseline_dir.join("gdppc-growth.csv")
    gdppc_baseline_path = baseline_dir.join("gdppc-merged-nohier.csv")
    nightlights_path = baseline_dir.join("nightlight_weight_normalized.csv")

    # Data to dump to temp files.
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

    baseline_df.to_csv(gdppc_baseline_path, index=False)
    growth_df.to_csv(gdppc_growth_path, index=False)
    df_nightlights.to_csv(nightlights_path, index=False)

    input_iam = "low"
    input_ssp = "SSP3"
    goal = np.array([ 2.,  4.,  8., 16., 32., 64., 64., 64., 64., 64., 64.])
    testprovider = gdppc.GDPpcProvider(iam=input_iam, ssp=input_ssp, stopyear=2020)
    actual = testprovider.get_timeseries(hierid="fooSPAM")
    np.testing.assert_array_equal(actual, goal)
