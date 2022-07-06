#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=main
#SBATCH -o logs/main.log
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=2
#SBATCH --time=72:00:00
#SBATCH --mem=64G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

NTASKS=16
NTHREAD=1
CONFIG_FILE="configs/default.yml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

# srun -n ${NTASKS} -c ${NTHREAD} python src/main.py
mpirun -np ${NTASKS} python src/main.py "${CONFIG_FILE}"
