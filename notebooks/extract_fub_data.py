from itertools import zip_longest
import numpy as np 
import pandas as pd
class FUBDataFile:
    __SKIPTO = 8
    __LINESTRUCTURE = {
        "IIII":5,
        "YYMM":5,
        "70hPa":4,
        "n70hPa":1,
        "50hPa":4,
        "n50hPa":1,
        "40hPa":4,
        "n40hPa":1,
        "30hPa":4,
        "n30hPa":1,
        "20hPa":4,
        "n20hPa":1,
        "15hPa":4,
        "n15hPa":1,
        "10hPa":4,
        "n10hPa":1
    }
    __NUMERIC =  ("70hPa","50hPa","40hPa","30hPa","20hPa","15hPa","10hPa")

    def __init__(self,path):
        self.path = path
        self.file = None
        self.struct = {
            k:[] for k in self.__LINESTRUCTURE
        }

    def __enter__(self):
        self.file = open(self.path)
        for i,line in enumerate(self.file):
            if i<=self.__SKIPTO: 
                continue
            stripline = line.strip()
            j = 0 
            for k,length in self.__LINESTRUCTURE.items():
                var = stripline[j:j+length].strip()
                if k == "YYMM":
                    self.struct[k].append("19"+var if int(var[:2]) >= 53 else "20" + var)
                else:
                    self.struct[k].append( int(var) if var else None)
                j+= length + 1
        return self

    def to_numpy(self):
        """Provides only the raw data without station or year in a 2d numpy array"""
        return np.transpose(np.array([np.array(self.struct[k],dtype=np.float) for k in self.__NUMERIC]))

    def to_pandas(self):
        df = pd.DataFrame.from_dict(self.struct)
        df["YYMM"] = pd.to_datetime(df["YYMM"],format="%Y%m")
        df = df.rename({"IIII":"Station","YYMM":"Date of Observation"})
        return df

    def __exit__(self,*args):
        if self.file is not None:
            self.file.close()
        self.struct = None
        self.file = None