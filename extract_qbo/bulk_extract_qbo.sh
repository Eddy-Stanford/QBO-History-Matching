#! /bin/bash
#SBATCH --array=0-99
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --time=01:00:00
#SBATCG --ntasks=4
source ~/.bashrc
conda activate
python extract_qbo.py $1/$SLURM_ARRAY_TASK_ID $2 $3 --output-name "${SLURM_ARRAY_TASK_ID}_QBO_${2}_${3}.nc" --latitude_range=5
