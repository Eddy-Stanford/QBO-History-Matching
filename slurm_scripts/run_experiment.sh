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
conda init
conda activate qbo_history_matching
expname=$(cat $expconfig | python3 -c "import sys;import json; print(json.load(sys.stdin)['name'])")
mkdir -p $SCRATCH/qbo_history_matching/$expname

# Run dispatcher
unset SLURM_MEM_PER_NODE
python experiment_init.py $expconfig
