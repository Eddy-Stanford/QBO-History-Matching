import argparse
from pathlib import Path
import re
import os
import shutil
import subprocess
import json
import jinja2
import pandas as pd
from history_matching.samples import SampleSpace
if 'SLURM_JOBID' not in os.environ:
    raise RuntimeError("This script can only be accessed from a SLURM job")


HOME_EXECUTABLE = Path.home()/'MiMA'/'exp'/'exec.SH03_CEES'/'mima.x'
INPUT_FILES = Path.home()/'MiMA'/'input'

def load_config_file(path:str,wave:int):
    with open(path) as f:
        data = json.load(f)
    data['wave'] = wave
    if 'nruns_per_wave' not in data:
        data['nruns_per_wave'] = 100
    if 'time_to_run' not in data:
        data['time_to_run'] = 40
    if 'qbo_from' not in data:
        data['qbo_from'] = 20
    if 'qbo_to' not in data:
        data['qbo_to'] = data['time_to_run']
    return data


def get_jobid_from_stdout(stdout:bytes):
    stdout_str = stdout.decode()
    if (m:=re.search(r'[0-9]+',stdout_str)):
        return int(m[0])
    else:
        return None


def model_run(basedir,nruns_per_wave,time_to_run,concurrency=20,**kwargs):
    proc_status = subprocess.run(['sbatch',
        '--chdir',basedir,
        '--array',f'0-{nruns_per_wave-1}%{concurrency}',
        'model_run.sh',
        str(time_to_run),
    ],capture_output=True) 
    if proc_status.returncode == 0:
        jobid = get_jobid_from_stdout(proc_status.stdout)
        return jobid
    else:
        raise RuntimeError("Unable to dispatch model run job")


def get_template(name='input.nml.template'):
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(name)
    return template

def write_namefile(dir,template,**params):
    with open(os.path.join(dir,'input.nml'),'w') as input_namefile:
        input_namefile.write(template.render(**params))

def get_wave_base_dir(name,wave,**kwargs):
    base = os.path.expandvars(f'$SCRATCH/qbo_history_matching/{name}/wave_{wave}')
    os.makedirs(base)
    return base

def get_exp_base_dir(name,**kwargs):
    return os.path.expandvars(f"$SCRATCH/qbo_history_matching/{name}")

def get_samples(wave,**kwargs)-> pd.DataFrame:
    if wave == 0:
        return get_first_wave_samples(wave=wave,**kwargs)
    return get_n_wave_samples(wave=wave,**kwargs)

def get_first_wave_samples(sample_space,nruns_per_wave,**kwargs):
    bounds = {k:(v['min'],v['max']) for k,v in sample_space.items()}
    space = SampleSpace.from_bound_dict(bounds)
    samples = space.lhs_sample(nruns_per_wave,labelled=True)
    samples.index.names=['run_id']
    samples.to_csv(get_wave_paramlist_name(sample_space=sample_space,nruns_per_wave=nruns_per_wave,**kwargs))
    return samples

def get_wave_paramlist_name(wave,**kwargs):
    return os.path.join(get_exp_base_dir(wave=wave,**kwargs),f'{wave}_samples.csv')


def get_n_wave_samples(wave,**kwargs):
    next_path = get_wave_paramlist_name(wave=wave,**kwargs)
    if os.path.isfile(next_path):
        return pd.read_csv(next_path)
    raise RuntimeError("No samples are available for this wave! ")


def positive_int(val):
    val = int(val)
    if val <= 0:
        raise argparse.ArgumentTypeError('Value must be positive')
    return val

def create_run_dirs(base:str,run_id:int)->str:
    run_dir =os.path.join(base,str(run_id).zfill(2))
    os.makedirs(run_dir)
    ## Copy Executable
    shutil.copy(HOME_EXECUTABLE,os.path.join(run_dir,'mima.x'))
    ## Copy Input files
    shutil.copytree(INPUT_FILES,os.path.join(run_dir),dirs_exist_ok=True)
    ## Make RESTART dir
    os.makedirs(os.path.join(run_dir,'RESTART'))
    return run_dir

def get_job_number(stdout:str)->int:
    return int(re.match(r'[a-zA-Z]*([0-9]+)',stdout).group(1))

def qbo_merge_run(wave_base,dependency_id,nruns_per_wave,qbo_from=20,qbo_to=40,**kwargs):
    proc_status = subprocess.run(['sbatch',
        '--dependency',f"afterok:{dependency_id}",
        '--array',f'0-{nruns_per_wave-1}:10',
        'extract_qbo/bulk_extract_qbo.sh',
        wave_base,
        qbo_from,
        qbo_to,
    ],capture_output=True) 
    if proc_status.returncode == 0:
        jobid = get_jobid_from_stdout(proc_status.stdout)
        return jobid
    else:
        raise RuntimeError("Unable to dispatch model run job")
      

def analysis_run(configfile,dependency_id,wave,**kwargs):
    proc_status = subprocess.run(['sbatch',
        '--chdir',get_exp_base_dir(wave=wave,**kwargs),
        '--dependency',f"afterok:{dependency_id}",
        'analysis_run.sh',
        configfile,
        wave
    ],capture_output=True) 
    if proc_status.returncode == 0:
        jobid = get_jobid_from_stdout(proc_status.stdout)
        return jobid
    else:
        raise RuntimeError("Unable to dispatch model run job")

def next_wave_run(configfile,dependency_id,wave,**kwargs):
    proc_status = subprocess.run(['sbatch',
        '--dependency',f"afterok:{dependency_id}",
        'run_wave.sh',
        configfile,
        wave
    ],capture_output=True) 
    if proc_status.returncode == 0:
        jobid = get_jobid_from_stdout(proc_status.stdout)
        return jobid
    else:
        raise RuntimeError("Unable to dispatch model run job")
      