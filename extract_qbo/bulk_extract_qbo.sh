#! /bin/bash
#SBATCH --array=0-99
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --time=01:00:00
#SBATCG --ntasks=4
source ~/.bashrc
conda activate
printf -v idx "%02d" $SLURM_ARRAY_TASK_ID
python extract_qbo.py $1/$idx $2 $3 --output-name "${SLURM_ARRAY_TASK_ID}_QBO_${2}_${3}.nc"
