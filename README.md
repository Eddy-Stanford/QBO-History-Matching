# README
This is the code and data repository used to perform the History Matching calibration on the AD99 non-orographic gravity wave parameterization. Inside the repository are:
* Scripts needed to dispatch a wave of MiMA model runs on a SLURM cluster (`dispatch_utils.py` and `wave_dispatcher.py`)
* Scripts to extract the QBO from the MiMA output (`extract_qbo`)
* Scripts to execute a history matching step based on model vs reference QBO (`analysis.py` and `qbo_utils`)
* Notebooks to produce graphical outputs of the history matching procedure 

The code in the repository extends the generic history matching code available [here](https://github.com/Eddy-Stanford/History-Matching-Core).

This repository is maintained by Robert King (robcking@stanford.edu)

## Obtaining model runs
This work utilized the Model of an idealized Moist Atmosphere GCM (Jucker and Gerber, 2017) which has the AD99 parameterization implemented within it. The scripts in this repository utilize an `apptainer` containerized version of MiMA which is available at https://github.com/Eddy-Stanford/MiMA on the `container` branch. All scripts look for a compiled container (e.g `mima.sif`) available at a path specified by the `$MIMAPATH` environment variable. 


## Experiment definition files
Inside of the `experiments` folder, JSON definitions for the individual history matching experiments can be found. These definitions configure the GCM settings as well as settings for the History Matching analysis. In the default case, experiments are present which vary the number of sample points taken each iteration of history matching. This is set in the `init_sample_space` variable in the JSON. Experiments are run within folder automatically generated from the `name` parameters 

The JSON file also defines the initial AD99 parameter sample space considered in history matching as well as the initial Latin Hypercube sample points chosen, for consistency with calibration with EKI. 

A history matching experiment file can be dispatched on a SLURM equipped cluster with the command:
```bash
sbatch slurm_scripts/run_experiment.sh <path-to-exp-file.json>
```
This will by default run the experiment within a directory defined by the `$SCRATCH` environment variable. 

## References
Jucker, M., Gerber, E.P., 2017. Untangling the Annual Cycle of the Tropical Tropopause Layer with an Idealized Moist Model. Journal of Climate 30, 7339–7358. https://doi.org/10.1175/JCLI-D-17-0127.1

