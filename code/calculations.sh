#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=calculations
#SBATCH -o logs/calculations.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=72:00:00
#SBATCH --mem=8G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

ntasks=8
nthreads=1

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

# srun -n ${ntasks} -c ${nthreads} python calculations.py
mpirun -np ${ntasks} python calculations.py
