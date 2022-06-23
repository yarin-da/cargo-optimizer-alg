# Cargo Optimizer Algorithm

This repository is part of the Cargo Optimizer project.

The codebase contains implementations of different algorithms. 

Also, a server written in python `http.server` that implements RESTful API (although we only require a single call).

## Heuristic Algorithm - RCH

This algorithm is very fast, because it takes many random steps in the process. 

The idea is to run this algorithm many times and pick the best solution out of them all.

## Heuristic Algoritm - Naive

A simple algorithm that sorts the packages based on volume. The bigger volume packages enter the container first.

## Linear Programming

The codebase uses `mip` python package that runs linear programming. The main challenge is figuring out the variable and constraints. 

The biggest con for this algorithm is the time it takes since linear programming goes through a lot of options.

## Demonstration

[Youtube Video](https://youtu.be/Zvjm5s7ZOZs)