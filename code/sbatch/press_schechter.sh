#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=press_schechter
#SBATCH -o logs/press_schechter.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=72:10:00
#SBATCH --mem=100G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

NTASKS=1
NTHREAD=1
CONFIG_FILE="configs/main.yaml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

# srun -n ${NTASKS} -c ${NTHREAD} python src/runners/press_schechter.py
mpirun -np ${NTASKS} python src/runners/press_schechter.py "${CONFIG_FILE}"
