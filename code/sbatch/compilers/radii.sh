#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/
. sbatch/compilers/iterator.sh

nodes=1
ntasks_per_node=1
cpus_per_task=16
timeout="72:00:00"
mem="380G"

task() {
    R="${1}"
    Z="${2}"
    S="${3}"

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
}

iterate