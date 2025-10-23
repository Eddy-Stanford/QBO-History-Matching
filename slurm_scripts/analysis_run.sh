#!/bin/bash
#SBATCH --job-name=wave_analysis
#SBATCH --cpus-per-task=16
#SBATCH --time=01:00:00
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --mail-type=FAIL,TIME_LIMIT_90
set -e
expconfig=$1
waveno=$2
conda init
conda activate qbo_history_matching
python analysis.py $expconfig $waveno

