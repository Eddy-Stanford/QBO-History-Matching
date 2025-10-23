#!/bin/bash
#SBATCH --job-name=wave_analysis
#SBATCH --cpus-per-task=16
#SBATCH --time=01:00:00
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --mail-type=FAIL,TIME_LIMIT_90
set -e
expconfig=$1
module load python/3.12.1
spack env activate mima_sh3
expname=$(cat $expconfig | python3 -c "import sys;import json; print(json.load(sys.stdin)['name'])")
source $SCRATCH/qbo_history_matching/$expname/env/bin/activate
python uq_analysis.py $expconfig

