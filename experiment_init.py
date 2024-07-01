import os
import shutil
import sys

import joblib

import dispatch_utils
from uq_dispatcher import uq_dispatch
from wave_dispatcher import wave_dispatch


def experiment_dispatch(config_file):
    config = dispatch_utils.load_config_file(config_file, 0)
    base = dispatch_utils.get_exp_base_dir(**config)
    space = dispatch_utils.get_sample_space_from_config(**config)

    ## DETERMINE TASK

    if "history_matching" in config:
        print("History Matching ")
        hm_config = config.pop("history_matching")
        if "init_space_samples" in config.get("sample_space", {}).get("samples"):
            shutil.copy(
                config["sample_space"]["samples"], os.path.join(base, "0_samples.csv")
            )
        else:
            initial_samples = space.lhs_sample(
                hm_config["nruns_per_wave"], labelled=True
            )
            initial_samples.to_csv(
                os.path.join(base, "0_samples.csv"), index_label="run_id"
            )
        joblib.dump(space, os.path.join(base, "0.space"))

        with open(
            os.path.join(base, f'{config["name"]}_wave_0.log'),
            mode="a",
            encoding="utf-8",
        ) as sys.stdout:
            wave_dispatch(config_file, 0)

    elif "uq" in config:
        with open(
            os.path.join(base, f'{config["name"]}_uq.log'), mode="a", encoding="utf-8"
        ) as sys.stdout:
            uq_dispatch(config_file)
    else:
        raise RuntimeError(
            "No task specified in configuration file. Must include either `uq` or `history_matching` key in the configuration file"
        )


if __name__ == "__main__":
    config_file = sys.argv[1]
    experiment_dispatch(config_file)
