import os
import pytest
if not os.getenv("IMPERICS_SHAREDDIR"):
    pytest.skip(
        "skipping test as no IMPERICS_SHAREDDIR environment variable set",
        allow_module_level=True
    )
from impactcommon.exogenous_economy import gdppc
from impactlab_tools.utils import files

provider_low = gdppc.GDPpcProvider('low', 'SSP3')
provider_high = gdppc.GDPpcProvider('high', 'SSP3')

# ZWE exists in both IAMs: check that correct and different

def test_zwe_low():
    helper(provider_low, 'ZWE.2.2', 188.74704269, 569.97540343, 576.72664619)

def test_zwe_high():
    helper(provider_high, 'ZWE.2.2', 607.12035717, 2618.03101405, 2731.7025934)

# ABW exists only in the high IAM: check that the same
    
def test_abw_low():
    helper(provider_low, 'ABW', 1411.21495327, 5180.55555556, 5321.58780557)

def test_abw_high():
    helper(provider_high, 'ABW', 1411.21495327, 5180.55555556, 5321.58780557)

# XYZ is not a country; check that starts same and grows differently
    
def test_xyz_low():
    if files.sharedpath('testing')[:11] == '/shares/gcp':
        helper(provider_low, 'XYZ.1.2', 7065.37128841, 12309.8299344, 12417.4055742)
    else:
        helper(provider_low, 'XYZ.1.2', 415.320976851, 1254.179869326625, 1269.0353748748823)

def test_xyz_high():
    if files.sharedpath('testing')[:11] == '/shares/gcp':
        helper(provider_high, 'XYZ.1.2', 7065.37128841, 15837.3384374, 16024.4588895)
    else:
        helper(provider_high, 'XYZ.1.2', 415.320976851, 1653.5117662281498, 1711.9155483103712)
        
def helper(provider, region, in2010, in2050, in2051):
    assert provider.get_startyear() <= 2010
    series = provider.get_timeseries(region)
    assert series[2010 - provider.get_startyear()] == pytest.approx(in2010)
    assert series[2050 - provider.get_startyear()] == pytest.approx(in2050)
    assert series[2051 - provider.get_startyear()] == pytest.approx(in2051)

if __name__ == '__main__':
    test_zwe_low()
    test_zwe_high()
    test_abw_low()
    test_abw_high()
    test_xyz_low()
    test_xyz_high()
    print("All tests passed.")

