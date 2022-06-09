#!/bin/bash

#SBATCH -p all
#SBATCH --job-name=calc_delta
#SBATCH -o out_calc_delta.log
#SBATCH --nodes=15
#SBATCH --ntasks-per-node=10
#SBATCH --cpus-per-task=1
#SBATCH --time=12:00:00
#SBATCH --mem=16G
# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)
#SBATCH --mail-type=ALL
#SBATCH --mail-user=s2222340@ed.ac.uk

#################

NTASKS=102
# NTHREADS=8
RADIUS = 50


parse_cli () {
    values=()
    while [[ ${#@} -gt 0 ]]; do
            case ${1} in
            -n|--n-tasks)
                    NTASKS="${1}"
                    echo "Running for '${NTASKS}' number of tasks."
                    shift 2
                    ;;
            -r|--radius)
                    RADIUS="${1}"
                    echo "Using a sphere radius of '${RADIUS}' Mpc."
                    shift 2
                    ;;
            --*|-*)
                    echo "Unrecognised flag: ${1}, ignoring"
                    shift 1
                    ;;
            *)
                    values+=("${1}")
                    shift 1
                    ;;
            esac
    done

    # if [[ ${#values} -ge 1 ]]; then
    #     IN=${values[0]}
    # fi
}

# Initialise the environment to run python
setup() {
    cd ${SLURM_SUBMIT_DIR}

    module purge
    source /home/brs/tmox/tmox_conda
    tmox_activate
    conda activate yt
}

# set up and run the python code
main() {
    setup
    # srun -n ${NTASKS} -c ${NTHREADS} python calc_delta.py
    mpirun -np ${NTASKS} python calc_delta.py -n ${NTASKS} -r ${RADIUS}
}

# Read the CLI input if given
if [[ ${#@} -gt 0 ]]; then
    parse_cli "${@}"
fi

# Run the code
main