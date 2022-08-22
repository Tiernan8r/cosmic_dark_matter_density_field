#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/
echo "Working from dir: ${PWD}"

RADII=$(cat ./sbatch/compilers/radii.txt)
REDSHIFTS=$(cat ./sbatch/compilers/redshifts.txt)
SIMULATIONS=$(cat ./sbatch/compilers/datasets.txt)

nodes=1
ntasks_per_node=1
cpus_per_task=4
timeout="24:00:00"
mem="1G"

COMMENT_REGEX="#([[:space:]])?.*"

YAML_RADII="\n"
while read R; do
    # Skip commented out entries
    if [[ "${R}" =~ $COMMENT_REGEX ]]; then
        continue
    fi

    YAML_RADII+="- ${R}\n"
done <./sbatch/compilers/radii.txt

YAML_REDSHIFTS="\n"
while read Z; do
    # Skip commented out entries
    if [[ "${Z}" =~ $COMMENT_REGEX ]]; then
        continue
    fi

    YAML_REDSHIFTS+="- ${Z}\n"
done <./sbatch/compilers/redshifts.txt

YAML_SIMULATIONS=""
while read S; do
    # Skip commented out entries
    if [[ "${S}" =~ $COMMENT_REGEX ]]; then
        continue
    fi

    YAML_SIMULATIONS+="  - ${S}\n"
done <./sbatch/compilers/datasets.txt

# ============
# CONFIG
# ============
job_name="std_dev"
out_name="./configs/${job_name}.yaml"

config_file="configs/${job_name}.yaml"
datatypes="!include defaults/radii_datatypes.yaml"

root="/disk12/legacy/"
sim_data="\n  root: ${root}\n  simulation_names:\n${YAML_SIMULATIONS}"

./sbatch/compilers/config.sh -r "${YAML_RADII}" -z "${YAML_REDSHIFTS}" -sd "${sim_data}" -dt "${datatypes}" "${config_file}" "${out_name}"
