import pytest
from impactcommon.exogenous_economy import gdppc

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
    helper(provider_low, 'XYZ.1.2', 7065.37128841, 13733.1439925, 13850.0256535)

def test_xyz_high():
    helper(provider_high, 'XYZ.1.2', 7065.37128841, 16281.0359747, 16496.9435173)
    
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
    print "All tests passed."

