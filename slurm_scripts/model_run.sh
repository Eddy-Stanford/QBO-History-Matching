#!/bin/bash
#SBATCH --job-name=mimarunforyears
#SBATCH --mem=32G
#SBATCH --time=56:00:00
#SBATCH --partition=serc
#SBATCH --output=%a.log
#SBATCH -c 1
#SBATCH --constraint=CPU_GEN:RME
#SBATCH --mail-type=FAIL,TIME_LIMIT_90
#SBATCH --signal=B:SIGUSR1@120

set -e
iterations=$1
printf -v idx "%02d" $SLURM_ARRAY_TASK_ID
cd $idx

echo "Running for " $iterations " years"

mimacontainer="${MIMAPATH:-/home/groups/aditis2/robcking/mima.sif}"

function cleanup(){
    echo "TIME LIMIT IS CLOSE...cleaning up and requeueing"
    
    echo "Move RESTART FILES"
}
trap 'cleanup' SIGUSR1

for ((i=1;i<=$iterations;i++))
do
    echo "Running year " $i
    # ## Implement backoff
    # for j in {1..5}
    # do
    #     echo "attempt ${j}"
    #      srun --ntasks $SLURM_NTASKS apptainer run $mimacontainer && break || sleep 15;
    # done
    srun --ntasks $SLURM_NTASKS apptainer run $mimacontainer &
    children=$!
    wait
    apptainer exec $mimacontainer /opt/MiMA/build/mppnccombine.singularity -r atmos_daily_${i}.nc atmos_daily.nc.????
    
    cp RESTART/*res* INPUT/
    [ ! -d restart_history/restart_$i ] && mkdir -p restart_history/restart_$i
    cp -r RESTART/*res* restart_history/restart_$i/
done
echo "done";

