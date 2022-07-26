#!/usr/bin/bash

# Default values:

# VALUES:
FILENAME=""
# FLAGS:
# SAMPLING="!include defaults/sampling.yaml"
# RADII="!include defaults/radii.yaml"
# REDSHIFTS="!include defaults/redshifts.yaml"
# SIM_DATA="!include defaults/sim_data.yaml"
# CACHES="!include defaults/caches.yaml"
# DATATYPES="!include defaults/datatypes.yaml"
# PLOTTING="!include defaults/plotting.yaml"
CACHES=""
DATATYPES=""
SAMPLING=""
RADII=""
REDSHIFTS=""
SIM_DATA=""
PLOTTING=""

usage () {
	echo -e "${0} - Compiles a config file."
	echo -e "USAGE:\n"
    echo -e "${0} [FLAGS] [VALUES]\n"
    echo -e "FLAGS:\n"
    echo "-h/--help:        Display this prompt."
    echo "-s/--sampling:    The config sampling parameters."
    echo "                  Defaults to ${SAMPLING}"
    echo "-r/--radii:       The config radii parameters."
    echo "                  Defaults to ${RADII}"
    echo "-z/--redshifts    The config redshift parameters."
    echo "                  Defaults to ${REDSHIFTS}"
    echo "-d/--sim-data:    The simulation data parameters."
    echo "                  Defaults to ${SIM_DATA}"
    echo "-t/--datatypes:   The simulation data types to run on."
    echo "                  Defaults to ${DATATYPES}"
    echo "-c/--caches:      The cache parameters."
    echo "                  Defaults to ${CACHES}"
    echo "-p/--plotting:    The plotting parameters."
    echo "                  Defaults to ${PLOTTING}"
    echo -e "VALUES:\n"
    echo "<file name>:      The full path to the output config filename"
}


parse_cli () {
	values=()
   	while [[ ${#@} -gt 0 ]]; do
        	case ${1} in
            	-h|--help)
                	usage
                	exit 0
                	;;
				-s|--sampling)
					SAMPLING="${2}"
					echo -e "Using sampling parameters: ${SAMPLING}\n"
					shift 2
					;;
                -r|--radii)
                    RADII="${2}"
                    echo -e "Using radii parameters: ${RADII}\n"
                    shift 2
                    ;;
                -z|--redshifts)
                    REDSHIFTS="${2}"
                    echo -e "Using redshift parameters: ${REDSHIFTS}\n"
                    shift 2
                    ;;
                -d|--sim-data)
                    SIM_DATA="${2}"
                    echo -e "Using sim data parameters: ${SIM_DATA}\n"
                    shift 2
                    ;;
                -c|--cache)
                    CACHES="${2}"
                    echo -e "Using cache parameters: ${CACHES}\n"
                    shift 2
                    ;;
                -t|--datatypes)
                    DATATYPES="${2}"
                    echo -e "Using datatypes parameters: ${DATATYPES}\n"
                    shift 2
                    ;;
                -p|--plotting)
                    PLOTTING="${2}"
                    echo -e "Using plotting parameters: ${PLOTTING}\n"
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

    if [[ ${#values} -ge 1 ]]; then
        FILENAME=${values[0]}
    else
        echo "Missing required filename!"
        exit 1
    fi
}

compile () {

    TEMPLATE="%YAML 1.2\n---\n"

    if [[ ! -z ${SAMPLING} ]]; then
        TEMPLATE+="sampling: ${SAMPLING}\n"
    fi

    if [[ ! -z ${RADII} ]]; then
        TEMPLATE+="radii: ${RADII}\n"
    fi

    if [[ ! -z ${REDSHIFTS} ]]; then
        TEMPLATE+="redshifts: ${REDSHIFTS}\n"
    fi

    if [[ ! -z ${SIM_DATA} ]]; then
        TEMPLATE+="sim_data: ${SIM_DATA}\n"
    fi

    if [[ ! -z ${CACHES} ]]; then
        TEMPLATE+="caches: ${CACHES}\n"
    fi

    if [[ ! -z ${DATATYPES} ]]; then
        TEMPLATE+="datatypes: ${DATATYPES}\n"
    fi

    if [[ ! -z ${PLOTTING} ]]; then
        TEMPLATE+="plotting: ${PLOTTING}\n"
    fi

    dir=$(dirname "${FILENAME}")
    mkdir -p "${dir}"

    echo "Compiling result to file: ${FILENAME}"
    echo -e "Output is:\n"
    echo -e ${TEMPLATE} | tee ${FILENAME}
}


if [[ ${#@} -gt 0 ]]; then
    parse_cli "${@}"
fi

if [[ -z "${FILENAME}" ]]; then
    echo "Filename unset!"
    exit 1
fi

compile 
