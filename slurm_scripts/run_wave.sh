#!/bin/bash
#SBATCH --job-name=wave_dispatcher
#SBATCH --nodes=1
#SBATCH --time=00:05:00
#SBATCH --mem=1G
#SBATCH --partition=serc
set -e
expconfig=$1
conda init
conda activate qbo_history_matching
unset SLURM_MEM_PER_NODE
expname=$(cat $expconfig | python3 -c "import sys;import json; print(json.load(sys.stdin)['name'])")
python3 wave_dispatcher.py "$@" >> $SCRATCH/qbo_history_matching/$expname/${expname}_wave_${2}.log
