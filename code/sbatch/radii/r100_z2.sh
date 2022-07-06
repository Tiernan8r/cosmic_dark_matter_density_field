#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=r100_z2
#SBATCH -o logs/radii/r100_z2.log
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
CONFIG_FILE="configs/radii/r100_Z2.yml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

# srun -n ${NTASKS} -c ${NTHREAD} python src/main.py
mpirun -np ${NTASKS} python src/main.py "${CONFIG_FILE}"
