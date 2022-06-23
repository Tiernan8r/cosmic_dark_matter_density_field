#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=calculations
#SBATCH -o calculations.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=2
#SBATCH --time=24:00:00
#SBATCH --mem=8G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

ntasks=4
nthreads=1

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

# srun -n ${ntasks} -c ${nthreads} python calculations.py
mpirun -np ${ntasks} python calculations.py
