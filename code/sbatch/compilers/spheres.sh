#! /usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/

RADII=(10 20 50 100 150 200 250 300 350 400 450 500 600 650)
REDSHIFTS=(0 1 2 3 4 5 6 7 8)

nodes=1
ntasks_per_node=1
cpus_per_task=4
timeout="72:00:00"
mem="16G"

for R in ${RADII[@]}; do
    for Z in ${REDSHIFTS[@]}; do
        radii_name="r${R}_z${Z}"
        job_name="sp_${radii_name}"

        # ============
        # SBATCH
        # ============

        out_name="./sbatch/spheres/${job_name}.sh"

        echo "JOB NAME: ${job_name}"
        echo "====================="

        logs="logs/spheres/${job_name}.log"
        config_file="configs/radii/${radii_name}.yaml"
        python="src/runners/sample.py"
        ./sbatch/compilers/sbatch.sh -l "${logs}" -n "${nodes}" --ntasks-per-node "${ntasks_per_node}" --cpus-per-task "${cpus_per_task}" -t "${timeout}" -m "${mem}" -c "${config_file}" -p "${python}" "${job_name}" "${out_name}"
    done
done