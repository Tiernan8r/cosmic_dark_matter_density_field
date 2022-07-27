#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/

COMMENT_REGEX="#([[:space:]])?.*"
while read R; do
    # Skip commented out entries
    if [[ "${R}" =~ $COMMENT_REGEX ]]; then
        continue
    fi

    while read Z; do
        # Skip commented out entries
        if [[ "${Z}" =~ $COMMENT_REGEX ]]; then
            continue
        fi

        while read S; do
            # Skip commented out entries
            if [[ "${S}" =~ $COMMENT_REGEX ]]; then
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

            ./sbatch/compilers/config.sh -r "${r}" -z "${z}" -c "${cache}" -d "${sim_data}" -t "${datatypes}" "${config_file}" "${out_name}"

        done <./sbatch/compilers/datasets.txt
    done <./sbatch/compilers/redshifts.txt
done <./sbatch/compilers/radii.txt
