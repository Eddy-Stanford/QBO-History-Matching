#!/bin/bash
#SBATCH --job-name=wave_dispatcher
#SBATCH --nodes=1
#SBATCH --time=00:05:00
#SBATCH --mem=1G
#SBATCH --partition=serc
expconfig=$1
module load python/3.9.0
expname=$(cat $expconfig | python3 -c "import sys;import json; print(json.load(sys.stdin)['name'])")
source $SCRATCH/qbo_history_matching/$expname/env/bin/activate
python wave_dispatcher.py "$@" >> ${expname}_wave_${2}.log
