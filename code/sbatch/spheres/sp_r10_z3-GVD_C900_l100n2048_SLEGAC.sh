#!/bin/bash
#SBATCH -p all
#SBATCH --job-name=sp_r10_z3-GVD_C900_l100n2048_SLEGAC
#SBATCH -o logs/spheres/sp_r10_z3-GVD_C900_l100n2048_SLEGAC.log
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
CONFIG_FILE="configs/radii/r10_z3-GVD_C900_l100n2048_SLEGAC.yaml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

mpirun -np ${NTASKS} python src/runners/sample.py "${CONFIG_FILE}"
