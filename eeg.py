import edfparser
from datetime import datetime
import numpy as np


class EEG:
    def __init__(self, sig, samp_rate):
        self.samp_rate = samp_rate
        self.signal = sig
    def subseq_t(self, sec_start, sec_end):
        """seconds to start in, seconds to end at"""
        ssa = sec_start*self.samp_rate
        ssb = sec_end*self.samp_rate
        return self.signal[ssa:ssb]

    def resample(self, new_rate):
        pass

    def __add__(self, otherEEG):
        if otherEEG.samp_rate != self.samp_rate:
            if self.samp_rate > otherEEG.samp_rate:
                b = otherEEG.resample(self.samp_rate)
                a = self
            else:
                b = self.resample(otherEEG.samp_rate)
                a = otherEEG
            return EEG(a.signal+b.signal, b.samp_rate)
        else:
            return EEG(self.signal+otherEEG.signal, self.samp_rate)

    def __mult__(self, scalar):
        return EEG(self.signal*scalar, self.samp_rate)





        
nasion = (70.0,0.0)
inion = (-80.,0.)

a1pt = (0., -70.)
a2pt = (0., +70.)

czpt = 
