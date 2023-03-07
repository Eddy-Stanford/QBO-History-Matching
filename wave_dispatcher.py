import argparse

import dispatch_utils

parser = argparse.ArgumentParser(description="")
parser.add_argument("configfile", type=str)
parser.add_argument("waveno", type=dispatch_utils.positive_int)

if __name__ == "__main__":
    args = parser.parse_args()
    config = dispatch_utils.load_config_file(args.configfile, wave=args.waveno)
    wave_base = dispatch_utils.get_wave_base_dir(**config)
    template = dispatch_utils.get_template()
    samples = dispatch_utils.get_samples(**config)

    for run, sample in samples.iterrows():
        run_dir = dispatch_utils.create_run_dirs(wave_base, run)
        if config.get("verbose"):
            print(f"[WRITTEN] namefile for {run} with parameters:{dict(**samples)} ")
        dispatch_utils.write_namefile(run_dir, template, **sample)

    modelrun_id = dispatch_utils.model_run(wave_base, **config)

    qbo_merge_id = dispatch_utils.qbo_merge_run(wave_base, modelrun_id, **config)

    analysis_id = dispatch_utils.analysis_run(args.configfile, qbo_merge_id, **config)

    if args.waveno + 1 < config["waves"]:
        dispatch_utils.next_wave_run(
            args.configfile,
            analysis_id,
            args.waveno + 1,
        )
