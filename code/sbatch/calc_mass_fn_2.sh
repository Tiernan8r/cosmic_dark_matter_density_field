#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=calc_mass_fn_2
#SBATCH -o logs/out_calc_mass_fn_2.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=2
#SBATCH --time=2:00:00
#SBATCH --mem=64G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

ntasks=1
nthreads=1

cd ${SLURM_SUBMIT_DIR}

. ../activate_environment.sh

srun -n ${ntasks} -c ${nthreads} python ../calc_mass_fn_2.py
# mpirun -np ${ntasks} python calc_mass_fn.py
