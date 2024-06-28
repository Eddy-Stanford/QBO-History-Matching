import argparse

import dispatch_utils

parser = argparse.ArgumentParser(description="")
parser.add_argument("configfile", type=str, help="Path to configuration file")
parser.add_argument(
    "waveno", type=dispatch_utils.positive_int, help="Wave number to execute"
)
parser.add_argument(
    "--force",
    action="store_true",
    help="Force this wave to run regardless of config file status",
)


def wave_dispatch(configfile: str, waveno: int, force=False):
    config = dispatch_utils.load_config_file(configfile, wave=waveno)
    wave_base = dispatch_utils.get_wave_base_dir(**config)
    template = dispatch_utils.get_template()
    samples = dispatch_utils.get_samples(**config)
    if "history_matching" not in config:
        raise KeyError(
            "No history_matching key present within input configuration file. This is required for history matching tasks"
        )
    hm_config = config.pop("history_matching")

    ## CHECK IF THIS WAVE SHOULD EVEN BE RUN
    if (
        waveno < hm_config.get("waves")
        and dispatch_utils.check_unconverged(waveno, **config, **hm_config)
    ) or force:
        ## CONFIGURE FOR RUN
        for run, sample in samples.iterrows():
            run_dir = dispatch_utils.create_run_dirs(wave_base, run)
            if config.get("verbose"):
                print(
                    f"[WRITTEN] namefile for {run} with parameters:{sample.to_dict()}"
                )
            dispatch_utils.write_namefile(run_dir, template, **sample, **hm_config)

        ### RUN WAVE
        if config.get("is_hotstart"):
            base_off = dispatch_utils.get_lastwave_least_implausible(
                **config, **hm_config
            )
            modelrun_id = dispatch_utils.hotstart_run(
                wave_base, base_off, **config, **hm_config
            )
        else:
            modelrun_id = dispatch_utils.model_run(wave_base, **config, **hm_config)
        ### ANALYSIS
        qbo_merge_id = dispatch_utils.qbo_merge_run(
            wave_base, modelrun_id, **config, **hm_config
        )

        analysis_id = dispatch_utils.analysis_run(
            configfile, qbo_merge_id, **config, **hm_config
        )

        dispatch_utils.next_wave_run(
            configfile,
            analysis_id,
            waveno + 1,
        )
    else:
        print("Finished...")


if __name__ == "__main__":
    args = parser.parse_args()
    wave_dispatch(args.configfile, args.waveno, args.force)
