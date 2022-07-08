#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=sp_r20_z2
#SBATCH -o logs/spheres/sp_r20_z2.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=72:00:00
#SBATCH --mem=16G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

NTASKS=1
NTHREAD=1
CONFIG_FILE="configs/radii/r20_z2.yml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

# srun -n ${NTASKS} -c ${NTHREAD} python src/calc/main.py
mpirun -np ${NTASKS} python src/runners/sample.py "${CONFIG_FILE}"
