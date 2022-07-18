#!/bin/bash
#SBATCH -p all
#SBATCH --job-name=r100_z5-GVD_C700_l10n1024_SLEGAC
#SBATCH -o logs/radii/r100_z5-GVD_C700_l10n1024_SLEGAC.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=72:00:00
#SBATCH --mem=32G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

NTASKS=1
CONFIG_FILE="configs/radii/r100_z5-GVD_C700_l10n1024_SLEGAC.yaml"

cd ${SLURM_SUBMIT_DIR}

. activate_environment.sh

mpirun -np ${NTASKS} python src/main.py "${CONFIG_FILE}"

