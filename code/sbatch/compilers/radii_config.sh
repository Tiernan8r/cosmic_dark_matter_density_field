#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/

RADII=$(cat ./sbatch/compilers/radii.txt)
REDSHIFTS=$(cat ./sbatch/compilers/redshifts.txt)
SIMULATIONS=$(cat ./sbatch/compilers/datasets.txt)

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

            # ============
            # CONFIG
            # ============
            job_name="r${R}_z${Z}-${S}"
            out_name="./configs/radii/${job_name}.yaml"

            config_file="configs/radii/${job_name}.yaml"
            cache="!include ../defaults/radii_cache.yaml"
            datatypes="!include ../defaults/radii_datatypes.yaml"
            r="\n  - ${R}"
            z="\n  - ${Z}"

            root="/disk12/legacy/"
            sim_data="\n  root: ${root}\n  simulation_names:\n    - ${S}"

            ./sbatch/compilers/config.sh -r "${r}" -z "${z}" -c "${cache}" -d "${sim_data}" "${config_file}" "${out_name}"
        done
    done
done
