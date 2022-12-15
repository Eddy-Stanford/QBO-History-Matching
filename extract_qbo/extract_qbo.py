#! /usr/bin/env python
import sys
import xarray
import os
wd = sys.argv[1]
year_from = int(sys.argv[2])
year_to = int(sys.argv[3])
ds = None
os.chdir(wd)

for i in range(year_from,year_to):
	dsf = xarray.open_dataset(f"atmos_daily_{i}.nc",decode_times=False)
	if ds is None:
		ds = dsf.ucomp
	else:
		ds = xarray.concat((ds,dsf.ucomp),dim='time')
	dsf.close()
qbo = ds.sel(lat=slice(-10.0,10.0),).mean(dim=['lat','lon'])
qbo.to_netcdf(f"qbo_{year_from}_{year_to}.nc")

