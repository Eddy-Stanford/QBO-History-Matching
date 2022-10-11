from typing import List
import numpy as np
import argparse
import os
import subprocess
import jinja2
import re
import shutil
import csv
from pathlib import Path

if 'SLURM_JOBID' not in os.environ:
    raise RuntimeError("This script can only be accessed from a SLURM job")

CURRENT_CW = 35
CURRENT_BT= 0.0043

HOME_EXECUTABLE = Path.home()/'MiMa'/'bin'/'exec.SH03_CEES'/'mima.x'
INPUT_FILES = Path.home()/'MiMa'/'input'
BASE_DIR = os.path.expandvars('$SCRATCH/uncert_quant/$SLURM_JOBID')

def positive_int(val):
    val = int(val)
    if val <= 0:
        raise argparse.ArgumentTypeError('Value must be positive')
    return val

def create_run_dirs(run_id:int)->str:
    run_dir =os.path.join(BASE_DIR,str(run_id))
    os.makedirs(run_dir)
    ## Copy Executable
    shutil.copyfile(HOME_EXECUTABLE,'mima.x')
    ## Copy Input files
    shutil.copytree(INPUT_FILES,run_dir)
    ## Make RESTART dir
    os.makedirs(os.path.join(run_dir,'RESTART'))
    return run_dir

def get_job_number(stdout:str)->int:
    return int(re.match(r'[a-zA-Z]*([0-9]+)',stdout).group(1))

parser = argparse.ArgumentParser(description='Run Uncertanity Quantification experiments')
parser.add_argument('n_years',default=10,type=positive_int)
parser.add_argument('n_runs',default=10,type=positive_int)

if __name__ == '__main__':
    args = parser.parse_args()
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template('input.nml.template')

    Bt = CURRENT_BT*np.random.lognormal(size=(args.n_runs,))
    cw = CURRENT_CW*np.random.lognormal(size=(args.n_runs,))

    run_id:List[int] = [0]*args.n_runs
    os.chdir(BASE_DIR)

    for run in range(args.n_runs):
        run_cw = cw[run]
        run_Bt = Bt[run]
        run_dir = create_run_dirs(run)

        with open(os.path.join(run_dir,'input.nml','w')) as input_namefile:
            input_namefile.write(template.render(cw=run_cw,Bt_eq=run_Bt))

        # Dispatch task 
        # This calls sbatch so completes synchronously 
        proc = subprocess.run(['sbatch','model_run.sh',args.n_years,'--chdir',run_dir]) 
        run_id[run] = get_job_number(proc.stdout.decode())
    
    with open('paramlist.csv','w',newline='\n') as f:
        paramlist = csv.writer(f, delimiter=',',
                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
        paramlist.writerow(['run_id','Bt','cw'])
        paramlist.writerows([[run_id[i],Bt[i],cw[i]] for i in range(args.n_runs)])