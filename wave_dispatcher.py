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

if __name__ == "__main__":
    args = parser.parse_args()
    config = dispatch_utils.load_config_file(args.configfile, wave=args.waveno)
    wave_base = dispatch_utils.get_wave_base_dir(**config)
    template = dispatch_utils.get_template()
    samples = dispatch_utils.get_samples(**config)

    ## CHECK IF THIS WAVE SHOULD EVEN BE RUN
    if (
        args.waveno < config["waves"]
        and dispatch_utils.check_unconverged(args.waveno, **config)
    ) or args.force:
        ## CONFIGURE FOR RUN
        for run, sample in samples.iterrows():
            run_dir = dispatch_utils.create_run_dirs(wave_base, run)
            if config.get("verbose"):
                print(
                    f"[WRITTEN] namefile for {run} with parameters:{sample.to_dict()}"
                )
            dispatch_utils.write_namefile(run_dir, template, **sample)

        ### RUN WAVE
        if config.get("is_hotstart"):
            base_off = dispatch_utils.get_lastwave_least_implausible(**config)
            modelrun_id = dispatch_utils.hotstart_run(wave_base, base_off, **config)
        else:
            modelrun_id = dispatch_utils.model_run(wave_base, **config)
        ### ANALYSIS
        qbo_merge_id = dispatch_utils.qbo_merge_run(wave_base, modelrun_id, **config)

        analysis_id = dispatch_utils.analysis_run(
            args.configfile, qbo_merge_id, **config
        )

        dispatch_utils.next_wave_run(
            args.configfile,
            analysis_id,
            args.waveno + 1,
        )
    else:
        print("Finished...")
