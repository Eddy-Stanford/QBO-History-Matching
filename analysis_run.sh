#!/bin/bash
#SBATCH --job-name=wave_analysis
#SBATCH --cpu-per-task=16
#SBATCH --time=01:00:00
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --output=%a.log
expconfig=$1
waveno=$2
module load python/3.9.0
source ../env/bin/activate
python analysis.py $expconfig $waveno