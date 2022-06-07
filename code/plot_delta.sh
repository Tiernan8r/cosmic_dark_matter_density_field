#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=plot_delta
#SBATCH -o out.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=2:00:00
#SBATCH --mem=1G

# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

cd ${SLURM_SUBMIT_DIR}

# Load your anaconda module if needed

module purge
source /usr/local/anaconda/3.9/etc/profile.d/conda.sh
conda activate base

python plot_delta.py
