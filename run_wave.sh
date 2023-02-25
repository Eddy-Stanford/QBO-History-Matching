#!/bin/bash
#SBATCH --job-name=wave_dispatcher
#SBATCH --nodes=1
#SBATCH --time=00:05:00
#SBATCH --mem=1G
#SBATCH --partition=serc
expconfig=$1
waveno=$2
module load python/3.9.0
source $SCRATCH/qbo_history_matching/$expname/env/bin/activate
python wave_dispatcher.py $expconfig $waveno
