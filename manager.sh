#!/bin/bash
#SBATCH --job-name=mima
#SBATCH --nodes=1
#SBATCH --time=20:00:00
#SBATCH --mem=1G
#SBATCH --partition=serc
python uncertaintymanager.py $1
