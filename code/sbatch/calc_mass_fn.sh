#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=calc_mass_fn
#SBATCH -o logs/out_calc_mass_fn.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=2:00:00
#SBATCH --mem=16G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

ntasks=1
nthreads=1

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

srun -n ${ntasks} -c ${nthreads} python calc_mass_fn.py
# mpirun -np ${ntasks} python calc_mass_fn.py
