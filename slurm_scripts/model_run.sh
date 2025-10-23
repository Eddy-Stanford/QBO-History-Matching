#!/bin/bash
#SBATCH --job-name=mimarunforyears
#SBATCH --mem-per-cpu=1G
#SBATCH --time=48:00:00
#SBATCH --partition=serc
#SBATCH --output=%a.log
#SBATCH -c 1
#SBATCH --mail-type=FAIL,TIME_LIMIT_90
#SBATCH --constraint CPU_GEN:GEN
set -e
iterations=$1
printf -v idx "%02d" $SLURM_ARRAY_TASK_ID
cd $idx

spack env activate mima_sh4

echo "Running for " $iterations " years"
for ((i=1;i<=$iterations;i++))
do
    echo "Running year " $i
    ## Implement backoff
    for j in {1..5}
    do
        echo "attempt ${j}"
        srun --ntasks $SLURM_NTASKS mima && break || sleep 15;
    done
    mppnccombine -r atmos_daily_${i}.nc atmos_daily.nc.????
    
    cp RESTART/*res* INPUT/
    [ ! -d restart_history/restart_$i ] && mkdir -p restart_history/restart_$i
    cp -r RESTART/*res* restart_history/restart_$i/
done
echo "done";

