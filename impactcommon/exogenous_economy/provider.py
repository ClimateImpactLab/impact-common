class SpaceTimeProvider(object):
    def __init__(self, iam, ssp, startyear):
        self.iam = iam
        self.ssp = ssp
        self.startyear = startyear
        
    def get_startyear(self):
        return self.startyear

    def get_timeseries(self, region):
        raise NotImplementedError()
