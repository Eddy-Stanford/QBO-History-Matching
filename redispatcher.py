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
    reruns = []
    for run in filter(lambda x: os.path.isdir(os.path.join(args.in_dir,x)),os.listdir(args.in_dir)):
        if os.path.isfile(os.path.join(args.in_dir,run,f"atmos_daily_{args.run_to}.nc")):
            continue
        if os.path.isdir(os.path.join(args.in_dir,run,'restart_history',f'restart_{args.restart_from}')):
            reruns.append(run)
    print(f"Submitting restart files for: {reruns}" )
    if reruns:
        subprocess.run([
            'sbatch',
            '--chdir',args.in_dir,
            '--array=' + ','.join(reruns) + '%20',
            'model_rerun.sh',
            args.restart_from,
            args.run_to,
        ])
    ### rollback all to restart_from IF availabel
    