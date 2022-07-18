#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/

RADII=$(cat ./sbatch/compilers/radii.txt)
REDSHIFTS=$(cat ./sbatch/compilers/redshifts.txt)
SIMULATIONS=$(cat ./sbatch/compilers/datasets.txt)

num_sp_samples=1000

for R in ${RADII[@]}; do
    for Z in ${REDSHIFTS[@]}; do
        for S in ${SIMULATIONS[@]}; do
            # ============
            # CONFIG
            # ============
            job_name="r${R}_z${Z}-${S}"
            out_name="./configs/radii/${job_name}.yaml"

            config_file="configs/radii/${job_name}.yaml"
            cache="!include ../defaults/radii_cache.yaml"
            r="\n  - ${R}"
            z="\n  - ${Z}"
            sampling="\n  num_sp_samples: ${num_sp_samples}"

            root="/disk12/legacy/"
            sim_data="\n  root: ${root}\n  simulation_names:\n    - ${S}"

            ./sbatch/compilers/config.sh -r "${r}" -z "${z}" -c "${cache}" -s "${sampling}" -d "${sim_data}" "${config_file}" "${out_name}"
        done
    done
done