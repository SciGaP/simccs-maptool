import io
import logging
import os
import shutil

logger = logging.getLogger(__name__)

# TODO: clients of module can set keys on this of BaseData directories that should be cached
cached_cost_surfaces = {}


def create_scenario_dir(
    basepath, dataset_dir, sources, sinks, mps=None, solution=None, scenario="scenario1"
):
    """Create scenario directory structure populated with inputs."""
    dataset_dirname = os.path.basename(dataset_dir)
    local_dataset_dir = os.path.join(basepath, dataset_dirname)
    os.makedirs(local_dataset_dir, exist_ok=True)
    # Symlink in the BaseData directory for the dataset
    basedata_dir = os.path.join(local_dataset_dir, "BaseData")
    if not os.path.exists(basedata_dir):
        os.symlink(os.path.join(dataset_dir, "BaseData"), basedata_dir)
    # Create a scenario directory
    scenario_dir = os.path.join(local_dataset_dir, "Scenarios", scenario)
    os.makedirs(scenario_dir, exist_ok=True)
    # Write Sources, Sinks and linear Transport
    _write_scenario_file(os.path.join(scenario_dir, "Sources", "Sources.txt"), sources)
    _write_scenario_file(os.path.join(scenario_dir, "Sinks", "Sinks.txt"), sinks)
    _write_scenario_file(
        os.path.join(scenario_dir, "Transport", "Linear.txt"),
        """ID	X (Con)	C (Con)	X (ROW)	C (ROW)
1	0.0762	0.1789	0.0069	0.1174
2	0.0162	0.4932	0.0009	0.1511
""",
    )
    if mps:
        _write_scenario_file(os.path.join(scenario_dir, "MIP", "mip.mps"), mps)
    if solution:
        _write_scenario_file(os.path.join(scenario_dir, "Results", "soln.sol"))


def _write_scenario_file(file_path, file_contents):
    file_dirname = os.path.dirname(file_path)
    if not os.path.exists(file_dirname):
        os.mkdir(file_dirname)
    with open(file_path, mode="wb") as scenario_file:
        src_file = file_contents
        if isinstance(src_file, str):
            src_file = io.BytesIO(src_file.encode())
        shutil.copyfileobj(src_file, scenario_file)


def get_sources_file(basepath, dataset_dir, scenario="scenario1"):
    return os.path.join(
        _get_scenario_dir(basepath, dataset_dir, scenario), "Sources", "Sources.txt"
    )


def get_sinks_file(basepath, dataset_dir, scenario="scenario1"):
    return os.path.join(
        _get_scenario_dir(basepath, dataset_dir, scenario), "Sinks", "Sinks.txt"
    )


def get_mps_file(basepath, dataset_dir, scenario="scenario1"):
    return os.path.join(
        _get_scenario_dir(basepath, dataset_dir, scenario), "MIP", "mip.mps"
    )


def get_candidate_network_file(basepath, dataset_dir, scenario="scenario1"):
    return os.path.join(
        _get_scenario_dir(basepath, dataset_dir, scenario),
        "Network",
        "CandidateNetwork",
        "CandidateNetwork.txt",
    )


def _get_scenario_dir(basepath, dataset_dir, scenario):
    dataset_dirname = os.path.basename(dataset_dir)
    return os.path.join(basepath, dataset_dirname, "Scenarios", scenario)


def write_mps_file(
    basepath,
    dataset_dirname,
    scenario,
    capital_recovery_rate=0.1,
    num_years=10,
    capacity_target=5,
):

    try:
        from jnius import autoclass

        DataStorer = autoclass("dataStore.DataStorer")
        data = DataStorer(basepath, dataset_dirname, scenario)
        Solver = autoclass("solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        # TODO: Use cached cost surface data for Lower48US dataset (although
        # ultimately only needed for candidate network)
        MPSWriter = autoclass("solver.MPSWriter")
        scenario_dir = os.path.join(basepath, dataset_dirname, "Scenarios", scenario)
        os.mkdir(os.path.join(scenario_dir, "MIP"))
        MPSWriter.writeCapPriceMPS(
            "mip.mps",
            data,
            capital_recovery_rate,
            num_years,
            capacity_target,
            basepath,
            dataset_dirname,
            scenario,
            1,  # modelVersion - 1 = cap
        )
    except Exception as e:
        logger.exception(
            "Error occurred when calling writeCapPriceMPS: " + str(e.stacktrace)
            if hasattr(e, "stacktrace")
            else str(e)
        )


def make_shapefiles(basepath, dataset_dirname, scenario, results_dir):
    try:
        from jnius import autoclass

        DataStorer = autoclass("dataStore.DataStorer")
        data = DataStorer(basepath, dataset_dirname, scenario)
        Solver = autoclass("solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        logger.debug(f"Scenario data loaded for {basepath}:{scenario}")
        # load the .mps/.sol solution
        solution = data.loadSolution(results_dir, -1)  # timeslot
        logger.debug(f"Solution loaded from {results_dir}")
        # generate shapefiles
        data.makeShapeFiles(results_dir, solution)
        logger.debug(
            f"Shape files created in {os.path.join(results_dir, 'shapeFiles')}"
        )
    except Exception as e:
        logger.exception(
            "Error occurred when calling makeShapeFiles: " + str(e.stacktrace)
            if hasattr(e, "stacktrace")
            else str(e)
        )


def load_solution(basepath, dataset_dirname, scenario, results_dir):
    try:
        from jnius import autoclass

        DataStorer = autoclass("dataStore.DataStorer")
        data = DataStorer(basepath, dataset_dirname, scenario)
        Solver = autoclass("solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        logger.debug(f"Scenario data loaded for {basepath}:{scenario}")
        # load the .mps/.sol solution
        solution = data.loadSolution(results_dir, -1)  # timeslot
        logger.debug("Solution loaded from {}".format(results_dir))
        return solution
    except Exception as e:
        logger.exception(
            "Error occurred when calling loadSolution: " + str(e.stacktrace)
            if hasattr(e, "stacktrace")
            else str(e)
        )
