#!/bin/bash
#SBATCH --job-name=ovenreadybrexit
#SBATCH --nodes=1
#SBATCH --tasks-per-node=16
#SBATCH --time=48:00:00
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --output=%a.log