#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/
echo "Working from dir: ${PWD}"

RADII=$(cat ./sbatch/compilers/radii.txt)
REDSHIFTS=$(cat ./sbatch/compilers/redshifts.txt)
SIMULATIONS=$(cat ./sbatch/compilers/datasets.txt)

nodes=1
ntasks_per_node=1
cpus_per_task=4
timeout="72:00:00"
mem="16G"

for R in ${RADII[@]}; do
    # Skip commented out entries
    if [[ $R == \#* ]]; then
        continue
    fi

    for Z in ${REDSHIFTS[@]}; do
        # Skip commented out entries
        if [[ $Z == \#* ]]; then
            continue
        fi

        for S in ${SIMULATIONS[@]}; do
            # Skip commented out entries
            if [[ $S == \#* ]]; then
                continue
            fi

            radii_name="r${R}_z${Z}-${S}"
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
done