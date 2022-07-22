#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=rho_bar
#SBATCH -o logs/rho_bar.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=24:00:00
#SBATCH --mem=8G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

NTASKS=1
NTHREAD=1
CONFIG_FILE="configs/rho_bar.yaml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

# srun -n ${NTASKS} -c ${NTHREAD} python src/runners/rho_bar.py
mpirun -np ${NTASKS} python src/runners/rho_bar.py "${CONFIG_FILE}"
