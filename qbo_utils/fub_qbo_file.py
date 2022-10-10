import numpy as np


class FUBDataFile:
    __SKIPTO = 8
    __LINESTRUCTURE = {
        "IIII": 5,
        "YYMM": 5,
        "70hPa": 4,
        "n70hPa": 1,
        "50hPa": 4,
        "n50hPa": 1,
        "40hPa": 4,
        "n40hPa": 1,
        "30hPa": 4,
        "n30hPa": 1,
        "20hPa": 4,
        "n20hPa": 1,
        "15hPa": 4,
        "n15hPa": 1,
        "10hPa": 4,
        "n10hPa": 1,
    }
    __NUMERIC = ["70hPa", "50hPa", "40hPa", "30hPa", "20hPa", "15hPa", "10hPa"]

    def __init__(self, path=None, file=None):
        self.path = path
        self.file = file
        self.struct = None

    def open(self):
        self.struct = {k: [] for k in self.__LINESTRUCTURE}
        if not self.file:
            self.file = open(self.path, encoding="utf-8")
        else:
            self.file.seek(0)

        for i, line in enumerate(self.file):
            if i <= self.__SKIPTO:
                continue
            stripline = line.strip()
            j = 0
            for k, length in self.__LINESTRUCTURE.items():
                var = stripline[j : j + length].strip()
                if k == "YYMM":
                    self.struct[k].append(
                        "19" + var if int(var[:2]) >= 53 else "20" + var
                    )
                else:
                    self.struct[k].append(int(var) if var else None)
                j += length + 1
        return self

    def to_numpy(self):
        """Provides only the raw data without station or year in a 2d numpy array"""
        return 0.1 * np.transpose(
            np.array(
                [np.array(self.struct[k], dtype=np.float32) for k in self.__NUMERIC]
            )
        )

    def to_pandas(self):
        import pandas as pd

        df = pd.DataFrame.from_dict(self.struct)
        df["YYMM"] = pd.to_datetime(df["YYMM"], format="%Y%m")
        df[self.__NUMERIC] = df[self.__NUMERIC] * 0.1
        df = df.rename(columns={"IIII": "Station", "YYMM": "Date of Observation"})
        return df

    def to_xarray(self):
        import xarray as xr

        df = self.to_pandas()
        nd = self.to_numpy()
        return xr.DataArray(
            nd,
            dims=("time", "p"),
            coords={
                "time": df["Date of Observation"].to_numpy(),
                "p": np.array([70, 50, 40, 30, 20, 15, 10]),
            },
        )

    def close(self, *args):
        if self.file is not None:
            self.file.close()
        self.struct = None
        self.file = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *args):
        return self.close(*args)
