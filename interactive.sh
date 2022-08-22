#!/bin/bash

# srun --cpus-per-task=8 --mem=16G --ntasks-per-node=1 --pty bash
srun -N 1 --ntasks-per-node=1 --pty bash
