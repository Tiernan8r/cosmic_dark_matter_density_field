#!/usr/bin/bash

# Default values:

# VALUES:
JOB_NAME="default"
FILENAME="/tmp/default.sh"
# FLAGS:
LOGS=""
NODES=1
NTASKS_PER_NODE=1
CPUS_PER_TASK=1
TIMEOUT="24:00:00"
MEMORY="1G"
CONFIG="configs/default.yaml"
PYTHON_FILE="src/main.py"

usage () {
	echo -e "${0} - Compiles an sbatch file."
	echo -e "USAGE:\n"
    echo -e "${0} [FLAGS] [VALUES]\n"
    echo -e "FLAGS:\n"
    echo "-h/--help:        Display this prompt."
    echo "-l/--logs:        The log file name, defaults to logs/<job name>.log"
    echo "-n/--nodes:       The number of nodes, defaults to 1."
    echo "--ntasks-per-node:The number of tasks performable per CPU node."
    echo "                  Defaults to ${NTASKS_PER_NODE}"
    echo "--cpus-per-task:  The number of CPUs dedicated to each task."
    echo "                  Defaults to ${CPUS_PER_TASK}"
    echo "-t/--timeout:     The timeout for the job (in hh:mm:ss)."
    echo "                  Defaults to ${TIMEOUT}"
    echo "-m/--memory:      The amount of RAM to allocate to the job."
    echo "                  Defaults to ${MEMORY}"
    echo "-c/--config:      The config file to use."
    echo "                  Defaults to '${CONFIG}'"
    echo "-p/--python:      The python code to run."
    echo "                  Defaults to '${PYTHON_FILE}'"
    echo -e "VALUES:\n"
    echo "<job name>:       The sbatch job name."
    echo "<file name>:      The output sbatch filename & path"
}


parse_cli () {
	values=()
   	while [[ ${#@} -gt 0 ]]; do
        	case ${1} in
            	-h|--help)
                	usage
                	exit 0
                	;;
				-l|--logs)
					LOGS="${2}"
					# echo "Using log file '${LOGS}'"
					shift 2
					;;
                -n|--nodes)
                    NODES="${2}"
                    echo "Setting number of nodes to: ${NODES}"
                    shift 2
                    ;;
                --ntasks-per-node)
                    NTASKS_PER_NODE="${2}"
                    echo "Setting number of tasks per node to: ${NTASKS_PER_NODE}"
                    shift 2
                    ;;
                --cpus-per-task)
                    CPUS_PER_TASK="${2}"
                    echo "Setting number of CPUs per task to: ${CPUS_PER_TASK}"
                    shift 2
                    ;;
                -t|--timeout)
                    TIMEOUT="${2}"
                    echo "Setting timeout to '${TIMEOUT}'"
                    shift 2
                    ;;
                -m|--memory)
                    MEMORY="${2}"
                    echo "Setting allocated memory to: ${MEMORY}"
                    shift 2
                    ;;
                -c|--config)
                    CONFIG="${2}"
                    echo "Setting config to '${CONFIG}'"
                    shift 2
                    ;;
                -p|--python)
                    PYTHON_FILE="${2}"
                    echo "Setting python script to '${PYTHON_FILE}'"
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

    if [[ ${#values} -ge 2 ]]; then
        JOB_NAME=${values[0]}
        FILENAME=${values[1]}
    else
        echo "Not enough script values provided!"
        exit 1
    fi
}

compile () {
	
    NTASKS=$(($NODES * $NTASKS_PER_NODE))

    TEMPLATE="#!/bin/bash\n#SBATCH -p all\n#SBATCH --job-name=${JOB_NAME}\n#SBATCH -o ${LOGS}\n#SBATCH --nodes=${NODES}\n#SBATCH --ntasks-per-node=${NTASKS_PER_NODE}\n#SBATCH --cpus-per-task=${CPUS_PER_TASK}\n#SBATCH --time=${TIMEOUT}\n#SBATCH --mem=${MEMORY}\n# email notifications (NONE, BEGIN, END, FAIL, REQUEUE, ALL)\n#SBATCH --mail-type=FAIL\n#SBATCH --mail-user=s2222340@ed.ac.uk\n\n#################\n\nNTASKS=${NTASKS}\nCONFIG_FILE=\"${CONFIG}\"\n\ncd \${SLURM_SUBMIT_DIR}\n\n. activate_environment.sh\n\nmpirun -np \${NTASKS} python ${PYTHON_FILE} \"\${CONFIG_FILE}\"\n"

    dir=$(dirname "${FILENAME}")
    mkdir -p "${dir}"

    echo "Compiling result to file: ${FILENAME}"
    echo -e "Output is:\n"
    echo -e ${TEMPLATE} | tee ${FILENAME}
}


if [[ ${#@} -gt 0 ]]; then
    parse_cli "${@}"
fi

# Default the log if unset:
if [[ -z "${LOGS}" ]]; then
    LOGS="logs/${JOB_NAME}.log"
fi
echo "Using log file '${LOGS}'"

compile 
