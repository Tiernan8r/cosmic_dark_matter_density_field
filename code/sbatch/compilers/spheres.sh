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
}

iterate
