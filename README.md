# OPPLOAD Experiments

This repo contains everything needed for executing the OPPLOAD experiments.

## Overview
The experiments were performed using Docker and the [MACI framework](https://maci-research.net/).

## Docker
Install Docker as required for your OS and build the image from the Dockerfile in this repo.

## MACI
Follow the instructions on the MACI homepage to use it. After installation, replace the `ExperimentTemplates` and `ExperimentFramework` folders in you `maci_data` folder.

## Execution
Start the built docker container and set the `BACKEND` environment variable to the running MACI backend. You can also use docker compose. Go the MACI backing using your webbrowser, create a new study and start either the ring or mobile experiment.

## Results
The result logs are stored on the machine where the MACI backend is running.

## Evaluation
Use the provided Jupyter Notebook file to evaluate the results.
