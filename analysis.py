import argparse
import os

import joblib
import numpy as np
import pandas as pd
import xarray as xr
from history_matching.emulator import GPEmulator, implausibility
from history_matching.samples import SampleSpace

import dispatch_utils
from qbo_utils.qbo_process import get_signal_period_amplitude
from qbo_utils.qbo_ref import fetch_qbo_file, get_reference_qbo


def get_qbo_period_amplitude(run_id, qbo_from, qbo_to, **config):
    path = f"{run_id.zfill(2)}/{run_id.zfill(2)}_QBO_{qbo_from}_{qbo_to}.nc"
    with xr.open_dataset(path) as ds:
        u = ds.ucomp.sel(pfull=10, method="nearest")
        periods, amplitudes = get_signal_period_amplitude(u, points_per_month=30)
    return (
        np.mean(periods),
        np.std(periods) / len(np.sqrt(periods)),
        np.mean(amplitudes),
        np.std(amplitudes) / len(np.sqrt(amplitudes)),
    )


parser = argparse.ArgumentParser(description="")
parser.add_argument("configfile", type=str)
parser.add_argument("waveno", type=dispatch_utils.positive_int)
if __name__ == "__main__":
    args = parser.parse_args()
    config = dispatch_utils.load_config_file(args.configfile, args.waveno)

    ## Make directory for run analysis
    os.makedirs("./analysis")
    df = pd.read_csv(f"../wave_{args.waveno}", index_col="run_id")
    ## Get QBO files and convert them to numpty

    ## TODO: This code is pretty hardcoded rn, if we decide to
    ## look in to using more params/more observables this will need to
    ## be overhauled.
    X = np.zeros((config["nruns_per_wave"], 2))
    y = np.zeros((config["nruns_per_wave"], 2))
    y_err = np.zeros((config["nruns_per_wave"], 2))

    for run, (row) in df.iterrows():
        X[run] = list(row)
        period, period_err, amplitude, amplitude_err = get_qbo_period_amplitude(
            run, **config
        )
        y[run] = [period, amplitude]
        y[run] = [period_err, amplitude_err]

    if config.get("verbose"):
        np.save("analysis/X.npy", X)
        np.save("analysis/y.npy", y)
        np.save("analysis/y_err.npy", y_err)

    period_ref, period_err_ref, amplitude_ref, amplitude_err_ref = get_reference_qbo(
        fetch_qbo_file(local_path="../qbo.dat")
    )

    ## EMULATOR
    emulator = GPEmulator()
    emulator.fit(X, y, y_err)

    if config.get("verbose"):
        joblib.dump(emulator, "analysis/emulator.gpe")

    current_sample_space: SampleSpace = joblib.load(f"../{args.waveno}.space")

    y_pred, y_pred_std = emulator.predict_over_space(
        current_sample_space, return_std=True, resolution=SampleSpace.DEFAULT_RESOLUTION
    )

    # Calculate implausibility
    imp_map = implausibility(y_pred,y_pred_std,np.array([period,amplitude]),np.array([period_err,amplitude_err]))

    ## Calculate New Non-implausable Space
    # Use 3 sigma threshold
    imp_cutoff = imp_map < 3 
    new_space = SampleSpace.from_xarray(imp_cutoff)
    new_space = new_space.intersection(current_sample_space)
    ## Sample from new space
    new_samples = new_space.uniform(config['nruns_per_wave'],labelled=True)
    

    ## Save samples and new space
    joblib.dump(f"../{args.waveno + 1}.space",new_space)
    new_samples.to_csv(f"../{args.waveno +1}_samples.csv")

    # Optional plotting code
    if config.get("verbose"):
        import matplotlib.pyplot as plt
        fig,(ax1,ax2,ax3) = plt.subplots(n_rows=1,n_cols=3,figsize=(14,6))
        CS = y_pred[0].plot.contour(levels=25)
        ax1.scatter(X[:,0],X[:,1],marker='x')
        ax1.clabel(CS,CS.levels,inline=True,fontsize=10)

        fig.savefig("analysis/space.png")

        