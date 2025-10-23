#!/bin/bash
#SBATCH --job-name=experiment_dispatcher
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH -c 8
#SBATCH --partition=serc
# Create run directory
set -e
expconfig=$1
module load python/3.12
module load netcdf-c
module load hdf5

expname=$(cat $expconfig | python3 -c "import sys;import json; print(json.load(sys.stdin)['name'])")
mkdir $SCRATCH/qbo_history_matching/$expname
cp $expconfig $SCRATCH/qbo_history_matching/$expname/config.json
# Recreate python env from scratch each run
echo "Creating virtual environment for experiment: ${expname}"
python3 -m venv $SCRATCH/qbo_history_matching/$expname/env
source $SCRATCH/qbo_history_matching/$expname/env/bin/activate
python -m pip install -r requirements.txt
# Run dispatcher
unset SLURM_MEM_PER_NODE
python experiment_init.py $expconfig
