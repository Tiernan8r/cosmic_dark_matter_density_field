#!/usr/bin/bash

echo "Working from: '${PWD}'"

echo "Clearing radii logs"
rm logs/radii/*

echo "Clearing sphere logs"
rm logs/spheres/*

echo "Clearing compiled radii configs"
rm configs/radii/*

echo "Clearing compiled radii sbatchs"
rm sbatch/radii/*

echo "Clearing compiled sphere sbatchs"
rm sbatch/spheres/*
