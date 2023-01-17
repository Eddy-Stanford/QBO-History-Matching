#! /usr/bin/env python
import xarray
import argparse
import os
import numpy as np

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Combine multiple atmos daily files into QBO profile")
	parser.add_argument("wd",type=str)
	parser.add_argument("year_from",type=int)
	parser.add_argument("year_to",type=int)
	parser.add_argument("--output-name",type=str,default=None)
	parser.add_argument("--latitude_range",default=5,type=float)

	args = parser.parse_args()

	if not args.output_name:
		args.output_name = f"qbo_{args.year_from}_{args.year_to}.nc"
	ds = None

	os.chdir(args.wd)

	for i in range(args.year_from,args.year_to):
		dsf = xarray.open_dataset(f"atmos_daily_{i}.nc",decode_times=False)
		if ds is None:
			ds = dsf.ucomp
		else:
			ds = xarray.concat((ds,dsf.ucomp),dim='time')
		dsf.close()
	ds = ds.sel(lat=slice(-args.latitude_range,args.latitude_range),)
	weights = np.cos(np.deg2rad(ds.lat))
	qbo = ds.weighted(weights).mean(dim=['lat','lon'])
	qbo.to_netcdf(args.output_name)

