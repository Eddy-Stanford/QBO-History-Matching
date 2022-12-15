#! /bin/bash
#SBATCH --array=0-99
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --time=05:00:00
#SBATCG --ntasks=4
source ~/.bashrc
conda activate
python extract_qbo.py $1/$SLURM_ARRAY_TASK_ID $2 $3
