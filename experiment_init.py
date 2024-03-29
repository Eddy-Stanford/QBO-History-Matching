import os
import shutil
import sys

import joblib
from history_matching.samples import SampleSpace

import dispatch_utils


def get_first_wave_space(sample_space: dict[str, dict], **kwargs):
    bounds = {k: (v["min"], v["max"]) for k, v in sample_space.items()}
    calc_space = SampleSpace.from_bound_dict(bounds)
    return calc_space


if __name__ == "__main__":
    config_file = sys.argv[1]
    config = dispatch_utils.load_config_file(config_file, 0)
    base = dispatch_utils.get_exp_base_dir(**config)
    space = get_first_wave_space(**config)
    if "init_space_samples" in config:
        shutil.copy(config["init_space_samples"], os.path.join(base, "0_samples.csv"))
    else:
        initial_samples = space.lhs_sample(config["nruns_per_wave"], labelled=True)
        initial_samples.to_csv(
            os.path.join(base, "0_samples.csv"), index_label="run_id"
        )
    joblib.dump(space, os.path.join(base, "0.space"))
