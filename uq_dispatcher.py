import argparse
import os

import numpy as np

import ces
import dispatch_utils

parser = argparse.ArgumentParser(description="Dispatch UQ run")
parser.add_argument("configfile", type=str, help="")


def uq_dispatch(configfile):
    config = dispatch_utils.load_config_file(configfile)
    exp_dir = dispatch_utils.get_exp_base_dir(**config)
    ## TODO: Make this space responsible for everything, should contain if EKI/HM
    space = dispatch_utils.get_sample_space_from_config(**config)
    template = dispatch_utils.get_template()
    if "uq" not in config:
        raise KeyError(
            "Cannot run Uncertainty Quantification w/o definition in configuration file. Exiting..."
        )
    uq_config = config.pop("uq")

    ## Draw Samples

    ### Draw History Matching Samples
    if uq_config.get("type", "history_matching") == "history_matching":
        if "random_state" in config:
            np.random.seed(config["random_state"])
        samples = space.uniform(uq_config["nruns"])

    ### Draw EKI Samples
    elif uq_config.get("type", "history_matching") == "eki":
        if "random_state" in config:
            np.random.seed(config["random_state"])
        samples = ces.get_ad99_ces(space=space, **uq_config, **config)
    else:
        raise ValueError(
            f"Unknown UQ type:{uq_config['type']}, must be one of `eki` or `history_matching` "
        )

    ### Write samples
    np.save(os.path.join(exp_dir, "samples.npy"), samples)
    wave_base = os.path.join(exp_dir, "uq")
    ## Create Runs
    for run, sample in enumerate(samples):
        run_dir = dispatch_utils.create_run_dirs(wave_base, run)
        if config.get("verbose"):
            print(f"[WRITTEN] namefile for {run} with parameters:{sample}")
        dispatch_utils.write_namefile(
            run_dir,
            template,
            cwtropics=sample[0],
            Bt_eq=sample[1],
            co2ppmv=uq_config.get("co2ppmv"),
        )
    ## Dispatch Runs
    modelrun_id = dispatch_utils.model_run(
        wave_base, nruns_per_wave=uq_config["nruns"], **config, **uq_config
    )

    ## Extract QBO Signal
    qbo_merge_id = dispatch_utils.qbo_merge_run(
        wave_base, modelrun_id, nruns_per_wave=uq_config["nruns"], **config, **uq_config
    )
    ## Dispatch UQ Analysis
    dispatch_utils.uq_analysis_run(configfile, qbo_merge_id, **config, **uq_config)
    print("Done...")


if __name__ == "__main__":
    args = parser.parse_args()
    uq_dispatch(parser.configfile)
