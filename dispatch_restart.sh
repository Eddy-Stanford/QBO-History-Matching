#!/bin/bash
#SBATCH --job-name=rerun
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --mem=1G
#SBATCH --partition=serc
DIRECTORY=$1
RESTART_FROM=$2
RESTART_TO=$3
# Create run directory
module load python/3.9.0
# Recreate python env from scratch each run
python3 -m venv $DIRECTORY/env
source $DIRECTORY/env/bin/activate
python3 -m pip install -r requirements.txt
# Run dispatcher
python redispatcher.py $DIRECTORY $RESTART_FROM $RESTART_TO
deactivate 
rm -rf $DIRECTORY/env