#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=r50_z0
#SBATCH -o logs/r50_z0.log
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
CONFIG_FILE="configs/r50_z0.yml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

# srun -n ${NTASKS} -c ${NTHREAD} python main.py
mpirun -np ${NTASKS} python main.py "${CONFIG_FILE}"