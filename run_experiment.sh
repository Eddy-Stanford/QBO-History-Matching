#!/bin/bash
#SBATCH --job-name=uncertquantmanager
#SBATCH --nodes=1
#SBATCH --time=20:00:00
#SBATCH --mem=1G
#SBATCH --partition=serc

# Create run directory
mkdir $SCRATCH/uncert_quant/$SLURM_JOBID
mkdir $SCRATCH/uncert_quant/$SLURM_JOBID/logs
# Run dispatcher
python dispatcher.py $1 > $SCRATCH/uncert_quant/$SLURM_JOBID/dispatcher.out
