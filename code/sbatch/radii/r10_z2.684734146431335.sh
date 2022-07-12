#!/bin/bash
#SBATCH -p all
#SBATCH --job-name=r10_z2.684734146431335
#SBATCH -o logs/radii/r10_z2.684734146431335.log
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
CONFIG_FILE="configs/radii/r10_z2.684734146431335.yaml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

mpirun -np ${NTASKS} python src/main.py "${CONFIG_FILE}"

