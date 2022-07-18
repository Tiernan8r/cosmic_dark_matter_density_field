#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/

RADII=$(cat ./sbatch/compilers/radii.txt)
REDSHIFTS=$(cat ./sbatch/compilers/redshifts.txt)
SIMULATIONS=$(cat ./sbatch/compilers/datasets.txt)

nodes=1
ntasks_per_node=1
cpus_per_task=8
timeout="72:00:00"
mem="32G"

for R in ${RADII[@]}; do
    for Z in ${REDSHIFTS[@]}; do
        for S in ${SIMULATIONS[@]}; do
            job_name="r${R}_z${Z}-${S}"

            # ============
            # SBATCH
            # ============

            out_name="./sbatch/radii/${job_name}.sh"

            echo "JOB NAME: ${job_name}"
            echo "====================="

            logs="logs/radii/${job_name}.log"
            config_file="configs/radii/${job_name}.yaml"

            ./sbatch/compilers/sbatch.sh -l "${logs}" -n "${nodes}" --ntasks-per-node "${ntasks_per_node}" --cpus-per-task "${cpus_per_task}" -t "${timeout}" -m "${mem}" -c "${config_file}" "${job_name}" "${out_name}"
        done
    done
done