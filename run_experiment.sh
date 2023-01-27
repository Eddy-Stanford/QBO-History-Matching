#!/bin/bash
#SBATCH --job-name=dispatch_uncert
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --mem=1G
#SBATCH --partition=serc
# Create run directory
mkdir $SCRATCH/uncert_quant/$SLURM_JOBID
module load python/3.9.0
# Recreate python env from scratch each run
python3 -m venv $SCRATCH/uncert_quant/$SLURM_JOBID/env
source $SCRATCH/uncert_quant/$SLURM_JOBID/env/bin/activate
python3 -m pip install -r requirements.txt
# Run dispatcher
python dispatcher.py "$@"
deactivate 
rm -rf $SCRATCH/uncert_quant/$SLURM_JOBID/env