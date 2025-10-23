import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import jinja2
import joblib
import pandas as pd
from history_matching.samples import SampleSpace

if "SLURM_JOBID" not in os.environ:
    raise RuntimeError("This script can only be accessed from a SLURM job")

INPUT_FILES = Path.home() / "MiMA" / "input"


def load_config_file(path: str, wave: Optional[int] = None):
    """
    Load and parse a configuration file in JSON format.

    Parameters:
    - path (str): The path to the configuration file.
    - wave (Optional[int]): The wave number to be included in the configuration data. If provided, it will be added to the data. If the configuration contains hotstart settings and the wave number is greater than or equal to the hotstart start value, the hotstart overrides will be applied.

    Returns:
    - dict: The parsed configuration data with optional wave and hotstart overrides applied.

    Raises:
    - FileNotFoundError: If the specified file does not exist.
    - json.JSONDecodeError: If the file content is not valid JSON.
    """
    data = dict()
    with open(path, encoding="utf-8") as f:
        data.update(json.load(f))
    if wave is not None:
        data["wave"] = wave
        if data.get("hotstart"):
            if data["hotstart"].get("start", 0) <= wave:
                # Override data
                data["is_hotstart"] = True
                data.update(data["hotstart"].get("overrides", {}))
    if data.get("verbose"):
        print(data)
    return data


def get_jobid_from_stdout(stdout: bytes):
    stdout_str = stdout.decode()
    if match := re.search(r"[0-9]+", stdout_str):
        return int(match[0])


def clean_env():
    """
    Return an environment free from any SLURM-related variables from this current environment.
    This is needed to prevent any conflicts
    """
    return {k: v for k, v in os.environ.items() if not k.startswith("SLURM")}


def model_run(
    basedir,
    nruns_per_wave,
    time_to_run=40,
    concurrency=20,
    hold=False,
    cpus=16,
    **kwargs,
):
    """
    Submit a batch job to run a model using SLURM.

    Parameters:
    - basedir (str): The base directory where the job will be executed.
    - nruns_per_wave (int): The number of runs per wave.
    - time_to_run (int, optional): The time to run the job in minutes. Default is 40.
    - concurrency (int, optional): The maximum number of concurrent jobs. Default is 20.
    - hold (bool, optional): Whether to hold the job. Default is False.
    - cpus (int, optional): The number of CPUs to allocate for the job. Default is 16.
    - kwargs (Any): Additional keyword arguments.

    Returns:
    - subprocess.CompletedProcess: The result of the subprocess.run call.
    """
    proc_status = subprocess.run(
        [
            "sbatch",
            "--ntasks",
            str(cpus),
            "--chdir",
            basedir,
            "--array",
            f"0-{nruns_per_wave-1}%{concurrency}",
            ("-H " if hold else "") + "slurm_scripts/model_run_sh4.sh",
            str(time_to_run),
        ],
        capture_output=True,
        check=True,
        env=clean_env(),
    )
    jobid = get_jobid_from_stdout(proc_status.stdout)
    if kwargs.get("verbose"):
        print(f"[DISPATCHED] Model run {jobid} dispatched")
    return jobid


def hotstart_run(
    basedir,
    base_off,
    nruns_per_wave,
    time_to_run,
    concurrency=20,
    hold=False,
    cpus=16,
    **kwargs,
):
    proc_status = subprocess.run(
        [
            "sbatch",
            "--ntasks",
            str(cpus),
            "--chdir",
            basedir,
            "--array",
            f"0-{nruns_per_wave-1}%{concurrency}",
            ("-H " if hold else "") + "slurm_scripts/hot_start.sh",
            str(time_to_run),
            base_off,
        ],
        capture_output=True,
        check=True,
        env=clean_env(),
    )
    jobid = get_jobid_from_stdout(proc_status.stdout)
    if kwargs.get("verbose"):
        print(f"[DISPATCHED] Model run {jobid} dispatched")
    return jobid


def get_template(name="input.nml.template"):
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(name)
    return template


def write_namefile(directory, template, **params):
    with open(
        os.path.join(directory, "input.nml"), "w", encoding="utf-8"
    ) as input_namefile:
        input_namefile.write(template.render(**params))


def get_wave_base_dir(name, wave, **kwargs):
    base = os.path.expandvars(f"$SCRATCH/qbo_history_matching/{name}/wave_{wave}")
    if not os.path.exists(base):
        os.makedirs(base)
    return base


def get_sample_space_from_config(sample_space: dict, **kwargs) -> SampleSpace:
    """
    Builds a sample space from the provided parsed config dictionary.
    """
    if "file" in sample_space:
        calc_space = joblib.load(sample_space["file"])
        if not isinstance(calc_space, SampleSpace):
            raise ValueError(
                "sample_space[file] does not correspond to a SampleSpace pickle."
            )
    if "from_bounds" in sample_space:
        bounds = {
            k: (v["min"], v["max"]) for k, v in sample_space["from_bounds"].items()
        }
        calc_space = SampleSpace.from_bounds_dict(bounds)
    if "xarray" in sample_space:
        import xarray

        with xarray.open_dataset(sample_space["xarray"]) as f:
            calc_space = SampleSpace.from_xarray(f)

    if "numpy" in sample_space:
        import numpy as np

        sample_space_np = np.load(sample_space["numpy"]["file"])
        calc_space = SampleSpace.from_numpy(
            sample_space_np, **sample_space_np["numpy"].get("coordinates", {})
        )
    return calc_space


def get_exp_base_dir(name, **kwargs):
    return os.path.expandvars(f"$SCRATCH/qbo_history_matching/{name}")


def get_wave_paramlist_name(wave, **kwargs):
    return os.path.join(get_exp_base_dir(wave=wave, **kwargs), f"{wave}_samples.csv")


def get_samples(wave, **kwargs):
    next_path = get_wave_paramlist_name(wave=wave, **kwargs)
    if os.path.isfile(next_path):
        return pd.read_csv(next_path, index_col="run_id")
    raise RuntimeError("No samples are available for this wave! ")


def positive_int(val):
    val = int(val)
    if val < 0:
        raise argparse.ArgumentTypeError("Value must be non negative")
    return val


def get_wave_analysis(name, wave, **kwargs):
    path = os.path.join(
        get_wave_base_dir(name, wave, **kwargs), "analysis", "analysis.csv"
    )
    if os.path.isfile(path):
        return pd.read_csv(path, index_col="run_id")
    raise ValueError("Unable to locate analysis file")


def get_lastwave_least_implausible(wave, **kwargs):
    last_path = get_wave_analysis(wave=wave - 1, **kwargs)
    target_run = last_path["implausibility"].argmin()
    return os.path.join(
        get_wave_base_dir(wave=wave - 1, **kwargs), f"{str(target_run).zfill(2)}"
    )


def create_run_dirs(base: str, run_id: int) -> str:
    run_dir = os.path.join(base, str(run_id).zfill(2))
    os.makedirs(run_dir)
    ## Copy Input files
    shutil.copytree(INPUT_FILES, os.path.join(run_dir), dirs_exist_ok=True)
    ## Make RESTART dir
    os.makedirs(os.path.join(run_dir, "RESTART"))
    return run_dir


def get_job_number(stdout: str) -> int:
    return int(re.match(r"[a-zA-Z]*([0-9]+)", stdout).group(1))


def qbo_merge_run(
    wave_base, dependency_id, nruns_per_wave, time_to_run, spinup, **kwargs
):
    proc_status = subprocess.run(
        [
            "sbatch",
            "--dependency",
            f"afterok:{dependency_id}",
            "--array",
            f"0-{nruns_per_wave-1}:10",
            "--output",
            f"{wave_base}/qbo_merge.log",
            "extract_qbo/bulk_extract_qbo.sh",
            str(wave_base),
            str(spinup),
            str(time_to_run),
        ],
        capture_output=True,
        check=True,
        env=clean_env(),
    )
    jobid = get_jobid_from_stdout(proc_status.stdout)
    if kwargs.get("verbose"):
        print(f"[DISPATCHED] QBO Merge Run job {jobid} dispatched")
    return jobid


def uq_analysis_run(configfile, dependency_id, **kwargs):
    base = get_exp_base_dir(**kwargs)
    wave_base = os.path.join(base, "uq")
    proc_status = subprocess.run(
        [
            "sbatch",
            "--dependency",
            f"afterok:{dependency_id}",
            "--output",
            f"{wave_base}/analysis.log",
            "slurm_scripts/uq_analysis.sh",
            configfile,
        ],
        capture_output=True,
        check=True,
        env=clean_env(),
    )
    if proc_status.returncode == 0:
        jobid = get_jobid_from_stdout(proc_status.stdout)
        if kwargs.get("verbose"):
            print(f"[DISPATCHED] Analysis job {jobid} dispatched")
        return jobid
    else:
        raise RuntimeError(
            f"Unable to dispatch analysis job with:{proc_status.stderr} ({proc_status.returncode})"
        )


def analysis_run(configfile, dependency_id, wave, **kwargs):
    wave_base = get_wave_base_dir(wave=wave, **kwargs)
    proc_status = subprocess.run(
        [
            "sbatch",
            "--dependency",
            f"afterok:{dependency_id}",
            "--output",
            f"{wave_base}/analysis.log",
            "slurm_scripts/analysis_run.sh",
            configfile,
            str(wave),
        ],
        capture_output=True,
        check=True,
        env=clean_env(),
    )
    if proc_status.returncode == 0:
        jobid = get_jobid_from_stdout(proc_status.stdout)
        if kwargs.get("verbose"):
            print(f"[DISPATCHED] Analysis job {jobid} dispatched")
        return jobid
    else:
        raise RuntimeError(
            f"Unable to dispatch analysis job with:{proc_status.stderr} ({proc_status.returncode})"
        )


def next_wave_run(configfile, dependency_id, next_wave):
    proc_status = subprocess.run(
        [
            "sbatch",
            "--dependency",
            f"afterok:{dependency_id}",
            "slurm_scripts/run_wave.sh",
            configfile,
            str(next_wave),
        ],
        capture_output=True,
        check=True,
        env=clean_env(),
    )
    jobid = get_jobid_from_stdout(proc_status.stdout)
    return jobid


def get_space_relative_area(s: SampleSpace, sample_space: dict):
    ## TODO: Put into history_matching_core
    sxr = s.to_xarray()
    dx = (sxr.cwtropics.max() - sxr.cwtropics.min()) / sxr.cwtropics.size
    dy = (sxr.Bt_eq.max() - sxr.Bt_eq.min()) / sxr.Bt_eq.size
    return float(dx * dy * sxr.sum()) / float(
        (sample_space["cwtropics"]["max"] - sample_space["cwtropics"]["min"])
        * (sample_space["Bt_eq"]["max"] - sample_space["Bt_eq"]["min"])
    )


def check_unconverged(
    currentwave: int,
    convergence_criterion: Optional[float] = None,
    sample_space: Optional[dict] = None,
    **config,
) -> bool:
    """
    Checks if relative areas are converged (and thus if another wave should occur)
    Returns true if relative difference between areas exceeds percentage "convergence_criterion"
    Returns false if relative difference between areas does not exceed and thus is converged.
    """
    if convergence_criterion is None or not currentwave:
        return True
    exp_base = get_exp_base_dir(**config)
    curspace: SampleSpace = joblib.load(
        os.path.join(exp_base, f"{currentwave-1}.space")
    )
    cur_relarea = get_space_relative_area(curspace, sample_space)
    nextspace: SampleSpace = joblib.load(os.path.join(exp_base, f"{currentwave}.space"))
    next_relarea = get_space_relative_area(nextspace, sample_space)
    if config.get("verbose"):
        print(
            f"[INFO] Current convergence test:{(cur_relarea - next_relarea) / cur_relarea}"
        )
        print(f"[INFO] Target for convergence:{convergence_criterion/100}")

    return (cur_relarea - next_relarea) / cur_relarea >= (convergence_criterion / 100)
