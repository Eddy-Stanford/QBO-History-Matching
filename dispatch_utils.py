import argparse
from pathlib import Path
import re
import os
import shutil
import subprocess
import jinja2
if 'SLURM_JOBID' not in os.environ:
    raise RuntimeError("This script can only be accessed from a SLURM job")


CURRENT_CW = 35
CURRENT_BT= 0.0043

HOME_EXECUTABLE = Path.home()/'MiMA'/'exp'/'exec.SH03_CEES'/'mima.x'
INPUT_FILES = Path.home()/'MiMA'/'input'

def get_jobid_from_stdout(stdout:bytes):
    stdout_str = stdout.decode()
    if (m:=re.search(r'[0-9]+',stdout_str)):
        return int(m[0])
    else:
        return None


def model_run(basedir,nruns,t,concurrency=20):
    proc_status = subprocess.run(['sbatch',
        '--chdir',basedir,
        '--array',f'0-{nruns-1}%{concurrency}',
        'model_run.sh',
        str(t),
    ],capture_output=True) 
    if proc_status.returncode == 0:
        jobid = get_jobid_from_stdout(proc_status.stdout)
        return jobid
    else:
        raise RuntimeError("Unable to dispatch model run job")


def get_template(name='input.nml.template'):
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template('input.nml.template')
    return template

def write_namefile(dir,template,cw,Bt):
    with open(os.path.join(dir,'input.nml'),'w') as input_namefile:
        input_namefile.write(template.render(cw=cw,Bt_eq=Bt))

def get_base_dir(expname:str):
    if expname:
        return os.path.expandvars(f'$SCRATCH/uncert_quant/{expname}')
    else:
        return os.path.expandvars('$SCRATCH/uncert_quant/$SLURM_JOBID')

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