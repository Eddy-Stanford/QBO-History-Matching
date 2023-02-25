#!/bin/bash
#SBATCH --job-name=experiment_dispatcher
#SBATCH --nodes=1
#SBATCH --time=00:05:00
#SBATCH --mem=1G
#SBATCH --partition=serc
# Create run directory
expconfig=$1
module load python/3.9.0
expname=$(cat $expconfig | python3 -c "import sys;import json; print(json.load(sys.stdin)['name'])")
mkdir $SCRATCH/qbo_history_matching/$expname
cp $expconfig $SCRATCH/qbo_history_matching/$expname/config.json
# Recreate python env from scratch each run
echo "Creating virtual environment for experiment"
python3 -m venv $SCRATCH/qbo_history_matching/$expname/env
source $SCRATCH/qbo_history_matching/$expname/env/bin/activate
python -m pip install -r requirements.txt
# Run dispatcher
python wave_dispatcher.py $1 0 