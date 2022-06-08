#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=calc_delta
#SBATCH -o out.log
#SBATCH --nodes=10
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=12:00:00
#SBATCH --mem=16G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

ntasks=102
# nthreads=8

cd ${SLURM_SUBMIT_DIR}

module purge
source /home/brs/tmox/tmox_conda
tmox_activate
conda activate yt

# srun -n ${ntasks} -c ${nthreads} python calc_delta.py
mpirun -np ${ntasks} python calc_delta.py
