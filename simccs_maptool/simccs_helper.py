import glob
import io
import logging
import os
import re
import shutil

logger = logging.getLogger(__name__)

# keys are the BaseData directories that should be cached
CACHED_COST_SURFACES = {}


def register_cost_surface_data_cache(dataset_dir):
    # Since the BaseData directory is the directory symlinked into the scenario
    # directory, use it's path as the key for cost surfaces that should be
    # cached
    real_basedata_dir = os.path.realpath(os.path.join(dataset_dir, "BaseData"))
    CACHED_COST_SURFACES[real_basedata_dir] = None


def create_scenario_dir(
    basepath,
    dataset_dir,
    sources,
    sinks,
    candidate_network=None,
    mps=None,
    solution=None,
    scenario="scenario1",
):
    """Create scenario directory structure populated with inputs.

    The basepath is assumed to be an empty directory. The dataset_dir's
    BaseData directory will be symlinked into the constructed scenario
    directory under basepath.
    """
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
    if candidate_network:
        _write_scenario_file(
            get_candidate_network_file(scenario_dir),
            candidate_network,
        )
    if mps:
        _write_scenario_file(os.path.join(scenario_dir, "MIP", "cap.mps"), mps)
    if solution:
        _write_scenario_file(os.path.join(scenario_dir, "Results", "soln.sol"))
    return scenario_dir


def _write_scenario_file(file_path, file_contents):
    file_dirname = os.path.dirname(file_path)
    if not os.path.exists(file_dirname):
        os.makedirs(file_dirname)
    with open(file_path, mode="wb") as scenario_file:
        src_file = file_contents
        if isinstance(src_file, str):
            src_file = io.BytesIO(src_file.encode())
        shutil.copyfileobj(src_file, scenario_file)


def get_sources_file(scenario_dir):
    return os.path.join(scenario_dir, "Sources", "Sources.txt")


def get_sinks_file(scenario_dir):
    return os.path.join(scenario_dir, "Sinks", "Sinks.txt")


def get_mps_file(scenario_dir):
    return next(glob.iglob(os.path.join(scenario_dir, "MIP", "*.mps")), None)


def get_candidate_network_file(scenario_dir):
    return os.path.join(
        scenario_dir, "Network", "CandidateNetwork", "CandidateNetwork.txt"
    )


def make_candidate_network_shapefiles(scenario_dir):
    try:
        basepath, dataset_dirname, scenario = _get_scenario_path_components(
            scenario_dir
        )
        cost_surface_data = _get_cached_cost_surface_data(basepath, dataset_dirname)
        from jnius import autoclass

        DataStorer = autoclass("dataStore.DataStorer")
        data = DataStorer(basepath, dataset_dirname, scenario)
        Solver = autoclass("solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        if cost_surface_data is not None:
            cost_surface_data.populate(data)
        results_dir = os.path.join(scenario_dir, "Network", "CandidateNetwork")
        # Must make the CandidateNetwork directory before calling
        # makeCandidateNetworkShapeFiles
        os.makedirs(results_dir, exist_ok=True)
        data.makeCandidateShapeFiles(results_dir)
    except Exception as e:
        logger.exception(
            "Error occurred when calling makeCandidateNetworkShapeFiles: "
            + str(e.stacktrace)
            if hasattr(e, "stacktrace")
            else str(e)
        )
        raise e


def _get_scenario_path_components(scenario_dir):
    """Return tuple of basepath, dataset dir name and scenario."""
    dataset_dir = os.path.dirname(os.path.dirname(scenario_dir))
    return (
        os.path.dirname(dataset_dir),  # basepath
        os.path.basename(dataset_dir),  # dataset directory name
        os.path.basename(scenario_dir),  # scenario name
    )


def write_mps_file(
    scenario_dir, capital_recovery_rate=0.1, num_years=10, capacity_target=5, filename=None
):

    if filename is not None and not filename.endswith(".mps"):
        raise Exception(f"Invalid filename {filename}: must end with .mps")
    try:
        basepath, dataset_dirname, scenario = _get_scenario_path_components(
            scenario_dir
        )
        cost_surface_data = _get_cached_cost_surface_data(basepath, dataset_dirname)
        from jnius import autoclass

        DataStorer = autoclass("dataStore.DataStorer")
        data = DataStorer(basepath, dataset_dirname, scenario)
        Solver = autoclass("solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        # TODO: really only need cost_surface_data if we don't have the
        # candidate network
        if cost_surface_data is not None:
            cost_surface_data.populate(data)
        MPSWriter = autoclass("solver.MPSWriter")
        os.mkdir(os.path.join(scenario_dir, "MIP"))
        MPSWriter.writeCapPriceMPS(
            data,
            capital_recovery_rate,
            num_years,
            capacity_target,
            basepath,
            dataset_dirname,
            scenario,
            "c",  # modelVersion = "c" for capture
        )
        if filename is not None:
            mps_fullpath = get_mps_file(scenario_dir)
            normalized_filename = re.sub(r'[^\w.]+', '_', filename)
            os.rename(mps_fullpath,
                      os.path.join(os.path.dirname(mps_fullpath), normalized_filename))
    except Exception as e:
        logger.exception(
            "Error occurred when calling writeCapPriceMPS: " + str(e.stacktrace)
            if hasattr(e, "stacktrace")
            else str(e)
        )
        raise e


def make_shapefiles(scenario_dir, results_dir):
    try:
        basepath, dataset_dirname, scenario = _get_scenario_path_components(
            scenario_dir
        )
        cost_surface_data = _get_cached_cost_surface_data(basepath, dataset_dirname)
        from jnius import autoclass

        DataStorer = autoclass("dataStore.DataStorer")
        data = DataStorer(basepath, dataset_dirname, scenario)
        Solver = autoclass("solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        logger.debug(f"Scenario data loaded for {basepath}:{scenario}")
        # TODO: really only need cost_surface_data if we don't have the
        # candidate network
        if cost_surface_data is not None:
            cost_surface_data.populate(data)
        # load the .mps/.sol solution
        solution = data.loadSolution(results_dir)
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
        raise e


def load_solution(scenario_dir, results_dir):
    try:
        basepath, dataset_dirname, scenario = _get_scenario_path_components(
            scenario_dir
        )
        cost_surface_data = _get_cached_cost_surface_data(basepath, dataset_dirname)
        from jnius import autoclass

        DataStorer = autoclass("dataStore.DataStorer")
        data = DataStorer(basepath, dataset_dirname, scenario)
        Solver = autoclass("solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        logger.debug(f"Scenario data loaded for {basepath}:{scenario}")
        # TODO: really only need cost_surface_data if we don't have the
        # candidate network
        if cost_surface_data is not None:
            cost_surface_data.populate(data)
        # load the .mps/.sol solution
        solution = data.loadSolution(results_dir)
        logger.debug("Solution loaded from {}".format(results_dir))
        return solution
    except Exception as e:
        logger.exception(
            "Error occurred when calling loadSolution: " + str(e.stacktrace)
            if hasattr(e, "stacktrace")
            else str(e)
        )
        raise e


def _get_cached_cost_surface_data(basepath, dataset_dirname):
    real_basedata_dir = os.path.realpath(
        os.path.join(basepath, dataset_dirname, "BaseData")
    )
    if real_basedata_dir in CACHED_COST_SURFACES:
        if CACHED_COST_SURFACES[real_basedata_dir] is None:
            CACHED_COST_SURFACES[real_basedata_dir] = _load_cost_surface_data(
                basepath, dataset_dirname
            )
        return CACHED_COST_SURFACES[real_basedata_dir]
    else:
        return None


def _load_cost_surface_data(basepath, dataset):
    try:
        logger.info(f"Loading {dataset} cost surface data ...")
        scenario = "scenario1"
        from jnius import autoclass

        DataStorer = autoclass("dataStore.DataStorer")
        Solver = autoclass("solver.Solver")
        CostSurfaceData = autoclass("maptool.CostSurfaceData")
        data = DataStorer(basepath, dataset, scenario)
        solver = Solver(data)
        data.setSolver(solver)
        data.loadNetworkCosts()
        cost_surface_data = CostSurfaceData()
        cost_surface_data.load(data)
        logger.info(f"Loaded {dataset} cost surface data")
        return cost_surface_data
    except Exception as e:
        logger.exception(
            "Error occurred when loading cost surface data: " + str(e.stacktrace)
        )
        return None
