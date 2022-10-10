import argparse
import os

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from history_matching.emulator import Emulator, chisquaredtest, implausibility2
from history_matching.samples import SampleSpace
from scipy.stats import sem
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

import dispatch_utils
from qbo_utils.qbo_process import get_signal_period_amplitude
from qbo_utils.qbo_ref import fetch_qbo_file, get_reference_qbo


def get_qbo_period_amplitude(run_id, **config):
    wave_base = dispatch_utils.get_wave_base_dir(**config)
    path = os.path.join(
        wave_base,
        f"{str(run_id).zfill(2)}",
        (
            f"{str(run_id).zfill(2)}_"
            f"QBO_{config['spinup']}"
            f"_{config['time_to_run']}.nc"
        ),
    )
    with xr.open_dataset(path) as ds:
        u = ds.ucomp.sel(pfull=10, method="nearest")
        if config.get("verbose"):
            fig, ax = plt.subplots()
            ax.plot(u)
            ax.set_xlabel("Time (days)")
            ax.set_ylabel("u @ 10hPa (m/s)")
            fig.savefig(os.path.join(wave_base, "analysis", f"u_{run_id}.png"))
            plt.close(fig)
        periods, amplitudes = get_signal_period_amplitude(
            u,
            smoothed_avg_months=config.get("months_to_smooth", 5),
            points_per_month=30,
        )
    if config.get("verbose"):
        print(f"Run:{run_id}, periods:{periods}")
        print(f"Run:{run_id}, amplitudes:{amplitudes}")
    return (
        np.mean(periods),
        sem(periods),
        np.mean(amplitudes),
        sem(amplitudes),
    )


parser = argparse.ArgumentParser(description="Run analysis on HM wave")
parser.add_argument("configfile", type=str)
parser.add_argument("waveno", type=dispatch_utils.positive_int)
if __name__ == "__main__":
    args = parser.parse_args()
    config = dispatch_utils.load_config_file(args.configfile, args.waveno)
    wave_base = dispatch_utils.get_wave_base_dir(**config)
    exp_base = dispatch_utils.get_exp_base_dir(**config)
    ## Make directory for run analysis
    os.makedirs(os.path.join(wave_base, "analysis"), exist_ok=True)
    df = dispatch_utils.get_samples(**config)
    ## Get QBO files and convert them to numpy

    ## TODO: This code is pretty hardcoded rn, if we decide to
    ## look in to using more params/more observables this will need to
    ## be overhauled.
    ## TODO: Deal with this TODO
    X_thisiter = np.zeros((config["nruns_per_wave"], 2))
    y_thisiter = np.zeros((config["nruns_per_wave"], 2))
    y_err_thisiter = np.zeros((config["nruns_per_wave"], 2))

    for run, row in df.iterrows():
        X_thisiter[run] = list(row)
        period, period_err, amplitude, amplitude_err = get_qbo_period_amplitude(
            run, **config
        )
        y_thisiter[run] = [period, amplitude]
        y_err_thisiter[run] = [period_err, amplitude_err]

    np.save(os.path.join(wave_base, "analysis", "X.npy"), X_thisiter)
    np.save(os.path.join(wave_base, "analysis", "y.npy"), y_thisiter)
    np.save(os.path.join(wave_base, "analysis", "y_err.npy"), y_err_thisiter)

    # Suboptimal
    X = np.concatenate(
        [
            *[
                np.load(
                    os.path.join(
                        dispatch_utils.get_wave_base_dir(
                            name=config["name"], wave=p_wave
                        ),
                        "analysis",
                        "X.npy",
                    )
                )
                for p_wave in range(args.waveno)
            ],
            X_thisiter,
        ]
    )
    y = np.concatenate(
        [
            *[
                np.load(
                    os.path.join(
                        dispatch_utils.get_wave_base_dir(
                            name=config["name"], wave=p_wave
                        ),
                        "analysis",
                        "y.npy",
                    )
                )
                for p_wave in range(args.waveno)
            ],
            y_thisiter,
        ]
    )
    y_err = np.concatenate(
        [
            *[
                np.load(
                    os.path.join(
                        dispatch_utils.get_wave_base_dir(
                            name=config["name"], wave=p_wave
                        ),
                        "analysis",
                        "y_err.npy",
                    )
                )
                for p_wave in range(args.waveno)
            ],
            y_err_thisiter,
        ]
    )

    ## Account for NaN values - just ignore
    badys = np.isnan(y).any(axis=1)
    X = X[~(badys)]
    y = y[~(badys)]
    y_err = y_err[~(badys)]

    if config.get("verbose"):
        print(f"y:{y} {y.shape}")
        print(f"y_err:{y_err} {y_err.shape}")

    period_ref, period_err_ref, amplitude_ref, amplitude_err_ref = get_reference_qbo(
        fetch_qbo_file(local_path=os.path.join(exp_base, "qbo.dat"))
    )

    ## EMULATOR
    emulator = Emulator(
        n_features=2,
        kernel=ConstantKernel() * RBF(length_scale_bounds=(0.05, 1)) + WhiteKernel(),
        random_state=config.get("random_state", 42),
        n_restarts_optimizer=config.get("n_restarts_optimizer", 0),
    )
    emulator.fit(X, y, y_err=y_err)

    if config.get("verbose"):
        joblib.dump(emulator, os.path.join(wave_base, "analysis", "emulator.gpe"))

    init_sample_space: SampleSpace = joblib.load(os.path.join(exp_base, "0.space"))

    y_pred, y_pred_std = emulator.predict_over_space(
        init_sample_space, return_std=True, resolution=SampleSpace.DEFAULT_RESOLUTION
    )

    # Calculate implausibility
    imp_map = implausibility2(
        y_pred,
        y_pred_std,
        np.array([period_ref, amplitude_ref]),
        np.array([period_err_ref, amplitude_err_ref]),
    )
    df["implausibility"] = implausibility2(
        xr.DataArray(y_thisiter.T),
        xr.DataArray(y_err_thisiter.T),
        np.array([period_ref, amplitude_ref]),
        np.array([period_err_ref, amplitude_err_ref]),
    ).to_numpy()
    df["period"] = y_thisiter.T[0]
    df["amplitude"] = y_thisiter.T[1]

    ## Calculate New Non-implausible Space
    # Use 3 sigma threshold
    imp_cutoff = chisquaredtest(imp_map, config.get("significance_level", 0.01))
    new_space = SampleSpace.from_xarray(imp_cutoff)
    ## Sample from new space
    previous_sample_space = joblib.load(os.path.join(exp_base, f"{args.waveno}.space"))
    new_space = new_space.intersection(previous_sample_space)
    new_samples = new_space.uniform(config["nruns_per_wave"], labelled=True)

    ## Save samples and new space
    joblib.dump(new_space, os.path.join(exp_base, f"{args.waveno + 1}.space"))
    new_samples.to_csv(
        os.path.join(exp_base, f"{args.waveno +1}_samples.csv"), index_label="run_id"
    )

    # Optional plotting code
    if config.get("verbose"):
        import matplotlib.patches as mpatches

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 6))
        CS = y_pred[0].plot.contour(ax=ax1, levels=25, x="cwtropics", y="Bt_eq")
        ax1.scatter(X[:, 0], X[:, 1], marker="x")
        ax1.clabel(CS, CS.levels, inline=True, fontsize=10)
        ax1.set_ylabel("$Bt_{eq}$")
        ax1.set_xlabel("$Cw_{tropics}$")
        ax1.set_title("QBO Period (months)")

        CS2 = y_pred[1].plot.contour(ax=ax2, levels=25, x="cwtropics", y="Bt_eq")
        ax2.scatter(X[:, 0], X[:, 1], marker="x")
        ax2.clabel(CS2, CS2.levels, inline=True, fontsize=10)
        ax2.set_xlabel("$Cw_{tropics}$")
        ax2.set_ylabel("$Bt_{eq}$")
        ax2.set_title("QBO Amplitude (m/s)")

        imp_map.plot.contour(ax=ax3, levels=25, x="cwtropics", y="Bt_eq")
        CS3 = (
            new_space.to_xarray()
            .astype(int)
            .interp(
                cwtropics=np.linspace(
                    config["sample_space"]["cwtropics"]["min"],
                    config["sample_space"]["cwtropics"]["max"],
                    1000,
                ),
                Bt_eq=np.linspace(
                    config["sample_space"]["Bt_eq"]["min"],
                    config["sample_space"]["Bt_eq"]["max"],
                    1000,
                ),
                kwargs={"fill_value": 0},
            )
            .astype(bool)
            .plot.contourf(
                x="cwtropics",
                y="Bt_eq",
                ax=ax3,
                alpha=0.3,
                cmap="RdYlGn",
                add_colorbar=False,
            )
        )
        ax3.scatter(X[:, 0], X[:, 1], marker="x")
        ax3.set_xlabel("$Cw_{tropics}$")
        ax3.set_ylabel("$Bt_{eq}$")
        ax3.legend(
            handles=[
                mpatches.Patch(
                    color="lightgreen", label="Next iteration non-implausible space"
                ),
                mpatches.Patch(color="pink", label="Next iteration implausible space"),
            ]
        )
        ax3.set_title("Implausibility")

        fig.savefig(os.path.join(wave_base, "analysis", "space.png"), dpi=300)

    df.to_csv(os.path.join(wave_base, "analysis", "analysis.csv"))
