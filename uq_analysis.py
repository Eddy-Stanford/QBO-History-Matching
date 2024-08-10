import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.stats import sem

import dispatch_utils
from qbo_utils.qbo_process import get_signal_period_amplitude

parser = argparse.ArgumentParser()
parser.add_argument("configfile", type=str)


if __name__ == "__main__":
    args = parser.parse_args()
    config = dispatch_utils.load_config_file(args.configfile)
    wave_base = "uq"
    exp_base = dispatch_utils.get_exp_base_dir(**config)
    if "uq" not in config:
        raise RuntimeError("Cant run analysis script for non `uq` config")
    uq_config = config.pop("uq")
    os.makedirs(os.path.join(exp_base, wave_base, "analysis"), exist_ok=False)
    means = []
    sems = []
    periods_points = []
    amplitudes_points = []

    for i in range(uq_config["nruns"]):
        path = os.path.join(
            exp_base,
            wave_base,
            str(i).zfill(2),
            f"{str(i).zfill(2)}_QBO_{uq_config['spinup']}_{uq_config['time_to_run']}.nc",
        )
        with xr.open_dataset(path) as ds:
            u = ds.ucomp.sel(pfull=10, method="nearest")
            if config.get("verbose"):
                fig, ax = plt.subplots()
                ax.plot(u)
                ax.set_xlabel("Time (days)")
                ax.set_ylabel("u @ 10hPa (m/s)")
                fig.savefig(os.path.join(exp_base, wave_base, "analysis", f"u_{i}.png"))

            periods, amplitudes = get_signal_period_amplitude(
                u,
                smoothed_avg_months=uq_config.get("months_to_smooth", 5),
                points_per_month=30,
            )
            if config.get("verbose"):
                print(f"Run:{i}, periods:{periods}")
                print(f"Run:{i}, amplitudes:{amplitudes}")
            mean_period = np.mean(periods)
            mean_amplitude = np.mean(amplitudes)
            sem_period = sem(periods)
            sem_amplitude = sem(amplitudes)

            means.append([mean_period, mean_amplitude])
            sems.append([sem_period, sem_amplitude])
            periods_points.extend(periods)
            amplitudes_points.extend(amplitudes)
    means = np.array(means)
    sems = np.array(sems)
    periods_points = np.array(periods_points)
    amplitudes_points = np.array(amplitudes_points)

    ## DUMP FILES
    np.save(os.path.join(exp_base, wave_base, "analysis", "means.npy"), means)
    np.save(os.path.join(exp_base, wave_base, "analysis", "sems.npy"), sems)
    np.save(
        os.path.join(exp_base, wave_base, "analysis", "periods.npy"), periods_points
    )
    np.save(
        os.path.join(exp_base, wave_base, "analysis", "amplitudes.npy"),
        amplitudes_points,
    )

    ## PLOT HISTOGRAM
    plt.figure()
    plt.scatter(means[:, 0], means[:, 1])
    plt.xlabel("Periods (months)")
    plt.ylabel("Amplitude (m/s)")
    plt.savefig(os.path.join(exp_base, wave_base, "analysis", "mean_histogram.png"))

    plt.figure()
    plt.scatter(periods_points, amplitudes_points)
    plt.xlabel("Periods (months)")
    plt.ylabel("Amplitude (m/s)")
    plt.savefig(
        os.path.join(exp_base, wave_base, "analysis", "sample_direct_histogram.png")
    )

    print("done")
