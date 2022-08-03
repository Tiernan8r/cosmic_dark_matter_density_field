#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=delta_new
#SBATCH -o logs/out.log
#SBATCH --nodes=13
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=4
#SBATCH --time=12:00:00
#SBATCH --mem=256G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

ntasks=102

cd ${SLURM_SUBMIT_DIR}

. ./activate_environment.sh

# srun -n ${ntasks} -c ${nthreads} python delta_new.py
mpirun -np ${ntasks} python delta_new.py
