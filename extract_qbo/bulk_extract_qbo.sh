#! /bin/bash
#SBATCH --mem-per-cpu=32G
#SBATCH --partition=serc
#SBATCH --time=01:00:00
#SBATCH -n 10
#SBATCH --mail-type=FAIL,TIME_LIMIT_90

module load python/3.12
source $1/../env/bin/activate
for i in {0..9}; do
    printf -v idx "%02d"  $((SLURM_ARRAY_TASK_ID+i))
    if [ -d $1/$idx ]
    then
        echo "working on " $1/$idx
        srun -n 1 -N 1 python extract_qbo/extract_qbo.py $1/$idx $2 $3 --output-name "${idx}_QBO_${2}_${3}.nc" --latitude_range=5 &
    fi
done
wait
echo "done"