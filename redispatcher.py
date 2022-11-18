import os
import subprocess
import argparse
# Dispatch a set of tasks for incomplete log files. 

parser = argparse.ArgumentParser(description='Restart runs that are incomplete and run until reach intended deadline.')
parser.add_argument('in_dir')
parser.add_argument('restart_from',default=20)
parser.add_argument('run_to',default=40)

if __name__ == '__main__':
    args = parser.parse_args()
    os.chdir(args.in_dir)
    reruns = []
    for run in filter(os.path.isdir,os.listdir()):
        if os.path.isfile(os.path.join(run,f"atmos_daily_{args.run_to}.nc")):
            continue
        if os.path.isdir(os.path.join(run,'restart_history',f'restart_{args.restart_from}')):
            reruns.append(run)

    subprocess.run([
        'sbatch',
        '--chdir',args.in_dir,
        '--array',','.join(reruns) + '%20',
        'model_rerun.sh',
        args.restart_from,
        args.restart_to,
    ])
    ### rollback all to restart_from IF availabel
    