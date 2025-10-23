#!/bin/bash
#SBATCH --job-name=hotstart
#SBATCH --time=48:00:00
#SBATCH --mem=16G
#SBATCH --partition=serc
#SBATCH --output=%a.log
#SBATCH -c 1
#SBATCH --constraint=CPU_GEN:RME
#SBATCH --mail-type=FAIL,TIME_LIMIT_90
set -e
iterations=$1
baseOff=$2
#Copy files
printf -v idx "%02d" $SLURM_ARRAY_TASK_ID
cd $idx
cp $baseOff/RESTART/*res* INPUT/
#
echo "Hot start running for " $iterations " years"
#

spacktivate mima_sh4

for ((i=1;i<=$iterations;i++))
do
    echo "Running year " $i
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
