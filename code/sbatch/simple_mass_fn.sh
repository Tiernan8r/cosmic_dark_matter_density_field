#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=simple_mass_fn
#SBATCH -o logs/simple_mass_fn.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --time=12:00:00
#SBATCH --mem=64G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

ntasks=1
nthreads=1

cd ${SLURM_SUBMIT_DIR}

. ../activate_environment.sh

srun -n ${ntasks} -c ${nthreads} python ../simple_mass_fn.py
