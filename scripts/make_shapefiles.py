#!/usr/bin/env python
import jnius_config
import os
import sys

jnius_config.add_options("-Djava.awt.headless=true")
# Java 11, JavaFX options
jnius_config.add_options("--module-path=/Users/machrist/lib/javafx-sdk-11.0.2/lib")
jnius_config.add_options("--add-modules=ALL-MODULE-PATH")
jnius_config.set_classpath(
    os.path.join(
        os.getcwd(),
        "simccs_maptool",
        "simccs",
        "lib",
        "simccs-app-1.0-jar-with-dependencies.jar",
    )
)
from jnius import autoclass  # noqa

# basepath = "/Users/machrist/Box/SimCCS Gateway/Datasets"
basepath = "/Users/machrist/Downloads"
# dataset = "10_2014_OrdosBasin"

# Indiana
# dataset = "11_2015_Indiana"
# scenario = "scenario1"
# results_dir = os.path.join(basepath, dataset, "Scenarios/scenario1/Results/5MT_yr")
# results_dir = os.path.join(basepath, dataset, "Scenarios/scenario1/Results/15MT_yr")

# Texas
dataset = "5_2011_TexasPanhandle"
scenario = "scenario1"
results_dir = os.path.join(basepath, dataset, "Scenarios/scenario1/Results/5MT_yr")

try:
    DataStorer = autoclass("simccs.dataStore.DataStorer")
    data = DataStorer(basepath, dataset, scenario)
    Solver = autoclass("simccs.solver.Solver")
    solver = Solver(data)
    data.setSolver(solver)
    solution = data.loadSolution(results_dir)
    data.makeShapeFiles(results_dir, solution)
except Exception as e:
    print(
        "Error occurred when generating shapefiles: " + str(e.stacktrace),
        file=sys.stderr,
    )
    raise
