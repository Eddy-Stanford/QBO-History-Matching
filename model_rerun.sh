#!/bin/bash
#SBATCH --job-name=rerunner
#SBATCH --nodes=1
#SBATCH --tasks-per-node=16
#SBATCH --time=48:00:00
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --output=%a.log
restart_from=$1
restart_to=$2
cd $SLURM_ARRAY_TASK_ID

## COPY restart files
echo "Copying restart files"
if [[ $restart_from -eq 0 ]]
then
    echo "Performing full clean"
    cp ~/MiMa/input/INPUT INPUT/
    rm -rf restart_history
    rm atmos*.nc
else  
    cp restart_history/restart_${restart_from}/* INPUT/
fi

iterations=$((${restart_to} - ${restart_from}))


echo "Running for " $iterations " years"
ulimit -s unlimited

# Use cees-beta stack
. /home/groups/s-ees/share/cees/spack_cees/scripts/cees_sw_setup-beta.sh

module purge
CEES_MODULE_SUFFIX="cees-beta"

module load devel gcc/10.
module load intel-${CEES_MODULE_SUFFIX}
module load mpich-${CEES_MODULE_SUFFIX}/
module load netcdf-c-${CEES_MODULE_SUFFIX}/
module load netcdf-fortran-${CEES_MODULE_SUFFIX}/
module load anaconda-${CEES_MODULE_SUFFIX}/

cwd=`pwd`

# Currently two libraries are not found in linking on SH03_CEES: libfabric and hwloc. Manually add them here.
export LIBFABRIC_PATH="/home/groups/s-ees/share/cees/spack_cees/spack/opt/spack/linux-centos7-zen2/intel-2021.4.0/libfabric-1.13.1-fcah2ztj7a4kigbly6vxqa7vuwesyxmr/lib/"
export HWLOC_PATH="/home/groups/s-ees/share/cees/spack_cees/spack/opt/spack/linux-centos7-zen2/intel-2021.4.0/hwloc-2.5.0-4yz4g5jbydc4euoqrbudraxssx2tcaco/lib/"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${LIBFABRIC_PATH}:${HWLOC_PATH}"


N_PROCS=16
PLATFORM=SH03_CEES
CCOMB=${HOME}/MiMA/bin/mppnccombine.${PLATFORM}
for ((i=$restart_from+1;i<=$restart_to;i++))
do 
    echo "Running year " $i
    srun --ntasks $N_PROCS mima.x
    $CCOMB -r atmos_daily_${i}.nc atmos_daily.nc.????
    $CCOMB -r atmos_avg_${i}.nc atmos_avg.nc.????
    $CCOMB -r atmos_davg_${i}.nc atmos_davg.nc.????
    $CCOMB -r atmos_dext_${i}.nc atmos_dext.nc.????

    cp RESTART/*res* INPUT/
    [ ! -d restart_history/restart_$i ] && mkdir -p restart_history/restart_$i
    cp -r RESTART/*res* restart_history/restart_$i/
done
echo "done";

