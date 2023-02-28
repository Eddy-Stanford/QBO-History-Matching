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
    wave_base = dispatch_utils.get_wave_base_dir(**config)
    path = os.path.join(
        wave_base,
        f"{str(run_id).zfill(2)}",
        f"{str(run_id).zfill(2)}_QBO_{qbo_from}_{qbo_to}.nc",
    )
    with xr.open_dataset(path) as ds:
        u = ds.ucomp.sel(pfull=10, method="nearest")
        if config.get("verbose"):
            fig, ax = plt.subplots()
            ax.plot(u)
            ax.set_xlabel("Time (days)")
            ax.set_ylabel("u @ 10hPa (m/s)")
            fig.savefig(os.path.join(wave_base, "analysis", "u.png"))
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
    wave_base = dispatch_utils.get_wave_base_dir(**config)
    exp_base = dispatch_utils.get_exp_base_dir(**config)
    ## Make directory for run analysis
    os.makedirs(os.path.join(wave_base, "analysis"), exist_ok=True)
    df = pd.read_csv(
        os.path.join(exp_base, f"{args.waveno}_samples.csv"), index_col="run_id"
    )
    ## Get QBO files and convert them to numpy

    ## TODO: This code is pretty hardcoded rn, if we decide to
    ## look in to using more params/more observables this will need to
    ## be overhauled.
    X = np.zeros((config["nruns_per_wave"], 2))
    y = np.zeros((config["nruns_per_wave"], 2))
    y_err = np.zeros((config["nruns_per_wave"], 2))

    for run, row in df.iterrows():
        X[run] = list(row)
        period, period_err, amplitude, amplitude_err = get_qbo_period_amplitude(
            run, **config
        )
        y[run] = [period, amplitude]
        y[run] = [period_err, amplitude_err]

    if config.get("verbose"):
        np.save(os.path.join(wave_base, "analysis", "X.npy"), X)
        np.save(os.path.join(wave_base, "analysis", "y.npy"), y)
        np.save(os.path.join(wave_base, "analysis", "y_err.npy"), y_err)

    period_ref, period_err_ref, amplitude_ref, amplitude_err_ref = get_reference_qbo(
        fetch_qbo_file(local_path=os.path.join(exp_base, "qbo.dat"))
    )

    ## EMULATOR
    emulator = GPEmulator()
    emulator.fit(X, y, y_err)

    if config.get("verbose"):
        joblib.dump(emulator, os.path.join(wave_base, "analysis", "emulator.gpe"))

    current_sample_space: SampleSpace = joblib.load(
        os.path.join(exp_base, f"{args.waveno}.space")
    )

    y_pred, y_pred_std = emulator.predict_over_space(
        current_sample_space, return_std=True, resolution=SampleSpace.DEFAULT_RESOLUTION
    )

    # Calculate implausibility
    imp_map = implausibility(
        y_pred,
        y_pred_std,
        np.array([period, amplitude]),
        np.array([period_err, amplitude_err]),
    )

    ## Calculate New Non-implausable Space
    # Use 3 sigma threshold
    imp_cutoff = imp_map < 3
    new_space = SampleSpace.from_xarray(imp_cutoff)
    new_space = new_space.intersection(current_sample_space)
    ## Sample from new space
    new_samples = new_space.uniform(config["nruns_per_wave"], labelled=True)

    ## Save samples and new space
    joblib.dump(os.path.join(exp_base, f"{args.waveno + 1}.space"), new_space)
    new_samples.to_csv(
        os.path.join(exp_base, f"{args.waveno +1}_samples.csv"), index_label="run_id"
    )

    # Optional plotting code
    if config.get("verbose"):
        import matplotlib.pyplot as plt

        fig, (ax1, ax2, ax3) = plt.subplots(n_rows=1, n_cols=3, figsize=(14, 6))
        CS = y_pred[0].plot.contour(levels=25)
        ax1.scatter(X[:, 0], X[:, 1], marker="x")
        ax1.clabel(CS, CS.levels, inline=True, fontsize=10)

        fig.savefig(os.path.join(wave_base, "analysis", "space.png"))
