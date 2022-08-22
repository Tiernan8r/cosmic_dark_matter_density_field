#!/usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/

iterate() {
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

                task "${R}" "${Z}" "${S}"

            done <./sbatch/compilers/datasets.txt
        done <./sbatch/compilers/redshifts.txt
    done <./sbatch/compilers/radii.txt
}

task() {
    echo "UNIMPLEMENTED!!!"
}