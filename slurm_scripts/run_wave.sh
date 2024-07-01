#!/bin/bash
#SBATCH --job-name=wave_dispatcher
#SBATCH --nodes=1
#SBATCH --time=00:05:00
#SBATCH --mem=1G
#SBATCH --partition=serc
set -e
expconfig=$1
module load python/3.12.1 
expname=$(cat $expconfig | python3 -c "import sys;import json; print(json.load(sys.stdin)['name'])")
source $SCRATCH/qbo_history_matching/$expname/env/bin/activate 
python3 wave_dispatcher.py "$@" >> $SCRATCH/qbo_history_matching/$expname/${expname}_wave_${2}.log
