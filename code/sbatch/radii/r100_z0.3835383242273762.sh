#!/bin/bash
#SBATCH -p all
#SBATCH --job-name=r100_z0.3835383242273762
#SBATCH -o logs/radii/r100_z0.3835383242273762.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=72:00:00
#SBATCH --mem=16G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

NTASKS=1
CONFIG_FILE="configs/radii/r100_z0.3835383242273762.yaml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

mpirun -np ${NTASKS} python src/main.py "${CONFIG_FILE}"

