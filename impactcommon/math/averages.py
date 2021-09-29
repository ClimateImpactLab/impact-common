import numpy as np
import numba as nb

@nb.njit 
def compiled_npmean(x):
    return np.mean(x).item()

@nb.njit 
def compiled_npmedian(x):
    return np.median(x).item()

@nb.njit 
def compiled_sum(x):
    return float(sum(x))
    
@nb.njit 
def compiled_npflipud(x):
    return np.flipud(x)

@nb.njit
def compiled_bucket_updater(curlen, length, sumval, value):
    if curlen >= length:
        sumval = (length - 1) * sumval / curlen + value
        if curlen > length:
            curlen = length
    else:
        sumval += value
        curlen += 1

    return curlen, length, sumval

@nb.njit
def compiled_kernelaverager_get(write_index, kernel, values):
    if write_index is None or write_index == 0:
        subkernel = kernel[-len(values):]
        out = np.dot(subkernel, values) / np.sum(subkernel)
    else:
        recentkernel = kernel[-write_index:]
        olderkernel = kernel[:-write_index]
        out = np.dot(recentkernel, values[:write_index]) + np.dot(olderkernel, values[write_index:])
    return out


class RunningStatistic(object):
    """
    General interface for an running summary statistic over N values.
    """
    def __init__(self, length):            
        self.length = length

    def update(self, value):
        "Add a new value to the running summary statistic."
        raise NotImplementedError()

    def get(self):
        "Get the current value of the running summary statistic."
        raise NotImplementedError()

class MemoryAverager(RunningStatistic):
    """
    Parent class for a running statistic that efficiently stores the previous N values for its computation.
    """
    def __init__(self, values, length):
        super(MemoryAverager, self).__init__(length)

        if len(values) >= length:
            self.values = np.array(values[-length:], dtype=np.float64)
            self.write_index = 0 # overwrite at this location next time
        else:
            self.values = np.array(values, dtype=np.float64)
            self.write_index = None # append next time

    def update(self, value):
        if self.write_index is not None:
            self.values[self.write_index] = value
            self.write_index = (self.write_index + 1) % self.length
        else:
            self.values = np.append(self.values, value) 
            if len(self.values) == self.length:
                self.write_index = 0

class MeanAverager(MemoryAverager):
    """
    Simple mean running average.
    """
    def get(self):
        return compiled_npmean(self.values)

class MedianAverager(MemoryAverager):
    """
    Simple median running average.
    """
    def get(self):
        return compiled_npmedian(self.values)

class BucketAverager(RunningStatistic):
    """
    Bucket average, equivalent to an exponential kernel or Bayesian update.
    """
    def __init__(self, values, length):
        super(BucketAverager, self).__init__(length)
        self.sumval = compiled_sum(values)
        self.curlen = len(values)

    def update(self, value):
        self.curlen, self.length, self.sumval = compiled_bucket_updater(self.curlen, self.length, self.sumval, value)

    def get(self):
        return self.sumval/self.curlen 

class KernelAverager(MemoryAverager):
    """
    Parent class for kernel-baesd averages.
    """
    def __init__(self, values, kernel):
        super(KernelAverager, self).__init__(values, len(kernel))
        self.kernel = compiled_npflipud(np.array(kernel) / compiled_sum(kernel))
    
    def get(self):
        return compiled_kernelaverager_get(self.write_index, self.kernel, self.values)

    def get_calculation(self):
        if self.write_index is None or self.write_index == 0:
            subkernel = self.kernel[-len(self.values):]
            return ' + '.join(["{0} * {1}".format(subkernel[ii] / compiled_sum(subkernel), self.values[ii]) for ii in range(len(subkernel))])
        else:
            recentkernel = self.kernel[-self.write_index:]
            olderkernel = self.kernel[:-self.write_index]
            return ' + '.join(["{0} * {1}".format(recentkernel[ii], self.values[ii]) for ii in range(len(recentkernel))]) + ' + '.join(["{0} * {1}".format(olderkernel[ii], self.values[self.write_index + ii]) for ii in range(len(olderkernel))])
        
class KernelMeanAverager(KernelAverager):
    """
    Kernel-based implementation of a simple running average.
    """
    def __init__(self, values, length=5):
        super(KernelMeanAverager, self).__init__(values, np.ones(length))

class BartlettAverager(KernelAverager):
    """
    Bartlett running average.
    """
    def __init__(self, values, length=5):
        super(BartlettAverager, self).__init__(values, compiled_npflipud(np.arange(length) + 1.))

def translate(cls, length, data):
    avg = cls([], length)
    result = []
    for datum in data:
        avg.update(datum)
        result.append(avg.get())

    return result

if __name__ == '__main__':
    for cls in [MeanAverager, MedianAverager, BucketAverager, KernelMeanAverager, BartlettAverager]:
        print(cls)
        avg = cls(np.array([0,1,2,3]), 5)
        print(avg.get(), (0 + 1 + 2 + 3) / 4.)
        avg.update(4)
        print(avg.get(), (0 + 1 + 2 + 3 + 4) / 5.)
        avg.update(5)
        print(avg.get(), (0 + 1 + 2 + 3 + 4 + 5) / 5.)

    clses = [MeanAverager, MedianAverager, BucketAverager, KernelMeanAverager, BartlettAverager]
    averages = [cls(np.zeros(25), 30) for cls in clses]
    averages[2] = BucketAverager(np.zeros(25), 15)

    print("input,mean,median,bucket,mean2,bartlett")
    
    for ii in range(5):
        for average in averages:
            average.update(0.)
        print('0,' + ','.join([str(average.get()) for average in averages]))
    
    for ii in range(35):
        for average in averages:
            average.update(1.)
        print('1,' + ','.join([str(average.get()) for average in averages]))

    
