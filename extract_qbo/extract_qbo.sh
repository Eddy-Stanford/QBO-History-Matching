#!/bin/bash
#SBATCH --time=60
#SBATCH --nodes=1
#SBATCH --partition=serc
#SBATCH --cpus-per-task=32
#SBATCH --ntasks=1
#SBATCH --mem=64G

source ~/.bashrc
conda activate
python extract_qbo.py $1 $2 $3 --output-name "${idx}_QBO_${2}_${3}.nc" --latitude_range=5
