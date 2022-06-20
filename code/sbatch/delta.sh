#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=delta
#SBATCH -o logs/delta.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --time=24:00:00
#SBATCH --mem=64G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

NTASKS=1
NTHREADS=1

cd ${SLURM_SUBMIT_DIR}
. activate_environment.sh

srun -n ${NTASKS} -c ${NTHREADS} python delta.py