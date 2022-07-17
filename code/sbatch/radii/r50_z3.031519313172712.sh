#!/bin/bash
#SBATCH -p all
#SBATCH --job-name=r50_z3.031519313172712
#SBATCH -o logs/radii/r50_z3.031519313172712.log
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
CONFIG_FILE="configs/radii/r50_z3.031519313172712.yaml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

mpirun -np ${NTASKS} python src/main.py "${CONFIG_FILE}"

