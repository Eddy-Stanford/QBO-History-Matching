import os
import re
from glob import glob

import numpy as np
import pandas as pd
import xarray as xr
from history_matching.emulator import Emulator
from history_matching.emulator.implausibility import likelihood
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from tqdm import tqdm

import dispatch_utils
from qbo_utils.qbo_ref import fetch_qbo_file, get_reference_qbo


def draw_ces_samples_uniform_prior(
    likelihood: xr.DataArray,
    coord_min: np.ndarray,
    coord_max: np.ndarray,
    coord_names,
    N=1000,
    delta=0.5,
    burn_in=500,
):
    """
    Draw CES samples via Metropolis-Hastings Algorithm
    """
    x0 = np.random.uniform(low=coord_min, high=coord_max)
    delta = delta * np.diag(coord_max - coord_min)
    samples = np.empty((N, 2))
    samples[0] = x0
    for n in tqdm(range(N - 1)):
        cur_sample = samples[n]
        next_sample = np.random.multivariate_normal(samples[n], delta**2)
        ## Assuming uniform prior
        prior_next = (
            1 / (coord_max - coord_min).prod()
            if (next_sample < coord_max).all() and (next_sample > coord_min).all()
            else 0
        )
        ## Assuming uniform prior
        prior_cur = (
            1 / (coord_max - coord_min).prod()
            if (next_sample < coord_max).all() and (next_sample > coord_min).all()
            else 0
        )
        likelihood_next = likelihood.interp(coords=dict(zip(coord_names, next_sample)))
        likelihood_cur = likelihood.interp(coords=dict(zip(coord_names, cur_sample)))
        accept = np.min(
            [1, (prior_next * likelihood_next) / (prior_cur * likelihood_cur)]
        )
        if np.random.random() < accept:
            samples[n + 1] = next_sample
        else:
            samples[n + 1] = cur_sample
    return samples[burn_in:]


def get_ad99_ces(
    eki_exp_dir,
    sample_space,
    delta,
    nruns,
    eki_up_to_wave=None,
    random_state=42,
    burn_in=10000,
    **config,
):
    """
    TODO: At some point this will need to be replaced with a better method that natively uses an "updated" sample space object.
    """
    exp_base = dispatch_utils.get_exp_base_dir(**config)
    eki_samples = np.array(
        [
            pd.read_csv(f, index_col="run_id")[
                [
                    "cwtropics",
                    "Bt_eq",
                    "period",
                    "amplitude",
                    "period_sem",
                    "amplitude_sem",
                ]
            ].to_numpy()
            for f in sorted(
                glob(os.path.join(eki_exp_dir, "output_*.csv")),
                key=lambda x: int(re.search(r"(?<=_)\d+(?=.csv)", x).group()),
            )[:eki_up_to_wave]
        ]
    )
    X = np.concatenate(eki_samples[:, :, [0, 1]], axis=0)
    y = np.concatenate(eki_samples[:, :, [2, 3]], axis=0)
    y_err = np.concatenate(eki_samples[:, :, [4, 5]], axis=0)

    # Handle NaN values by removing them.
    nanwhere = np.isnan(y).any(axis=1)
    X = X[~nanwhere]
    y = y[~nanwhere]
    y_err = y_err[~nanwhere]

    ## Use same emualator arch as King et al, 2024 for now

    em = Emulator(
        n_targets=2,
        kernel=ConstantKernel() * RBF(length_scale_bounds=(0.05, 1)) + WhiteKernel(),
        random_state=random_state,
    )
    em.fit(X, y, y_err=y_err)
    pred, predstd = em.predict_over_space(
        sample_space, return_std=True, resolution=1000
    )
    period, perioderr, amplitude, amplituderr = get_reference_qbo(
        fetch_qbo_file(local_path=os.path.join(exp_base, "qbo.dat"))
    )
    liklihood = likelihood(
        pred,
        predstd,
        np.array([period, amplitude]),
        np.array([perioderr, amplituderr]),
    ) / np.sqrt(
        (predstd**2 + np.array([perioderr, amplituderr])[:, None, None] ** 2).prod(
            dim="n_features"
        )
    )
    coord_min = [v[0] for v in sample_space.bounds_dict.values()]
    coord_max = [v[1] for v in sample_space.bounds_dict.values()]

    ces = draw_ces_samples_uniform_prior(
        liklihood,
        coord_min=coord_min,
        coord_max=coord_max,
        coord_names=sample_space.coord_labels,
        N=nruns + burn_in,
        burn_in=burn_in,
        delta=delta,
    )
    return ces
