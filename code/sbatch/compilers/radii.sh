#! /usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/

RADII=(10 20 50 100 150 200 250 300 350 400 450 500 600 650)
REDSHIFTS=(0 1 2 3 4 5 6 7 8)

nodes=1
ntasks_per_node=1
cpus_per_task=4
timeout="72:00:00"
mem="16G"

num_sp_samples=5000

for R in ${RADII[@]}; do
    for Z in ${REDSHIFTS[@]}; do
        job_name="r${R}_z${Z}"

        # ============
        # SBATCH
        # ============

        out_name="./sbatch/radii/${job_name}.sh"

        echo "JOB NAME: ${job_name}"
        echo "====================="

        logs="logs/radii/${job_name}.log"
        config_file="configs/radii/${job_name}.yaml"
        ./sbatch/compilers/sbatch.sh -l "${logs}" -n "${nodes}" --ntasks-per-node "${ntasks_per_node}" --cpus-per-task "${cpus_per_task}" -t "${timeout}" -m "${mem}" -c "${config_file}" "${job_name}" "${out_name}"

        # ============
        # CONFIG
        # ============
        cache="!include radii_cache.yaml"
        r="\n  - ${R}"
        z="\n  - ${Z}"
        sampling="\n  num_sp_samples: ${num_sp_samples}"
        ./sbatch/compilers/config.sh -r "${r}" -z "${z}" -c "${cache}" -s "${sampling}" "${config_file}"
    done
done