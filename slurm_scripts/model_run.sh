#!/bin/bash
#SBATCH --job-name=mimarunforyears
#SBATCH --mem-per-cpu=1G
#SBATCH --time=48:00:00
#SBATCH --partition=serc
#SBATCH --output=%a.log
#SBATCH -c 1
#SBATCH --constraint=CPU_GEN:RME
#SBATCH --mail-type=FAIL,TIME_LIMIT_90
set -e
iterations=$1
printf -v idx "%02d" $SLURM_ARRAY_TASK_ID
cd $idx

module purge
module load python/3.12
module load openmpi
module load netcdf-c 
module load netcdf-fortran
module load gcc/14

echo "Running for " $iterations " years"
mimaexec="${MIMAPATH:-/home/groups/aditis2/robcking/mima.x}"
# mimacontainer="${MIMAPATH:-/home/groups/aditis2/robcking/mima.sif}"

for ((i=1;i<=$iterations;i++))
do
    echo "Running year " $i
    ## Implement backoff
    for j in {1..5}
    do
        echo "attempt ${j}"
        srun --ntasks $SLURM_NTASKS $mimaexec && break || sleep 15;
    done
    mppnccombine -r atmos_daily_${i}.nc atmos_daily.nc.????
    
    cp RESTART/*res* INPUT/
    [ ! -d restart_history/restart_$i ] && mkdir -p restart_history/restart_$i
    cp -r RESTART/*res* restart_history/restart_$i/
done
echo "done";

