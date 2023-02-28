#! /bin/bash
#SBATCH --mem=32G
#SBATCH --partition=serc
#SBATCH --time=01:00:00
#SBATCH --ntasks=10
module load python/3.9.0
source $1/../env/bin/activate
for i in {0..9}; do
    printf -v idx "%02d"  $((SLURM_ARRAY_TASK_ID+i))
    echo "working on " $1/$idx
    [ -d $1/$idx ] && srun -n 1 python extract_qbo.py $1/$idx $2 $3 --output-name "${idx}_QBO_${2}_${3}.nc" --latitude_range=5 & 
done
wait
echo "done"