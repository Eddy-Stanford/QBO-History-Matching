#! /usr/bin/env python
import argparse
import os
from typing import List

import numpy as np
import xarray as xr


def concat_and_weight_qbo(
    input_files: List[str], latitude_range: float
) -> xr.DataArray:
    ds = None
    for f in input_files:
        dsf = xr.open_dataset(f, decode_times=False)
        if ds is None:
            ds = dsf.ucomp
        else:
            ds = xr.concat((ds, dsf.ucomp), dim="time")
        dsf.close()
    ds = ds.sel(
        lat=slice(-latitude_range, latitude_range),
    )
    weights = np.cos(np.deg2rad(ds.lat))
    return ds.weighted(weights).mean(dim=["lat", "lon"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Combine multiple atmos daily files into QBO profile"
    )
    parser.add_argument("wd", type=str)
    parser.add_argument("year_from", type=int)
    parser.add_argument("year_to", type=int)
    parser.add_argument("--output-name", type=str, default=None)
    parser.add_argument("--latitude_range", default=5, type=float)

    args = parser.parse_args()

    if not args.output_name:
        args.output_name = f"qbo_{args.year_from}_{args.year_to}.nc"

    paths = [
        os.path.join(args.wd, f"atmos_daily_{i}.nc")
        for i in range(args.year_from, args.year_to)
    ]
    qbo = concat_and_weight_qbo(paths, args.latitude_range)
    qbo.to_netcdf(os.path.join(args.wd, args.output_name))
    print(f"Written {args.output_name}")
