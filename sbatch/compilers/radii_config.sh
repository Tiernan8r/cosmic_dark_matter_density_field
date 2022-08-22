#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/
. sbatch/compilers/iterator.sh

task() {
    R="${1}"
    Z="${2}"
    S="${3}"

    # ============
    # CONFIG
    # ============
    job_name="r${R}_z${Z}-${S}"
    out_name="./configs/radii/${job_name}.yaml"

    config_file="configs/radii/${job_name}.yaml"
    cache="!include ../defaults/radii_cache.yaml"
    datatypes="!include ../defaults/radii_datatypes.yaml"
    tasks="!include ../defaults/radii_tasks.yaml"
    r="\n  - ${R}"
    z="\n  - ${Z}"

    root="/disk12/legacy/"
    sim_data="\n  root: ${root}\n  simulation_names:\n    - ${S}"

    ./sbatch/compilers/config.sh -r "${r}" -z "${z}" -c "${cache}" -sd "${sim_data}" -dt "${datatypes}" -t "${tasks}" "${config_file}" "${out_name}"
}

iterate
