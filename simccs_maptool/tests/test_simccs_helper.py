import os
import tempfile
import unittest

from simccs_maptool import datasets, simccs_helper


class TestSimCCSHelper(unittest.TestCase):
    def setUp(self):
        dataset_id = datasets.SOUTHEASTUS_DATASET_ID
        self.dataset_dir = datasets.get_dataset_dir(dataset_id)
        scenario_dir = os.path.join(self.dataset_dir, "Scenarios", "scenario1")
        with open(
            simccs_helper.get_sources_file(scenario_dir),
            "r"
        ) as sources, open(
            simccs_helper.get_sinks_file(scenario_dir),
            "r",
        ) as sinks, open(
            os.path.join(scenario_dir, "Results", "50MTyr", "solution.sol"),
            "r",
        ) as solution, open(
            os.path.join(scenario_dir, "Results", "50MTyr", "mip.mps"),
            "r",
        ) as mps, open(
            simccs_helper.get_candidate_network_file(scenario_dir),
            "r",
        ) as candidate_network:
            self.sources = sources.read()
            self.sinks = sinks.read()
            self.solution = solution.read()
            self.mps = mps.read()
            self.candidate_network = candidate_network.read()

    def test_create_scenario_dir(self):
        with tempfile.TemporaryDirectory() as datasets_basepath:

            scenario_dir = simccs_helper.create_scenario_dir(
                datasets_basepath, self.dataset_dir, self.sources, self.sinks
            )

            # BaseData directory should be symlinked into scenario directory
            self.assertNotEqual(
                os.path.join(self.dataset_dir, "BaseData"),
                os.path.join(
                    os.path.dirname(os.path.dirname(scenario_dir)), "BaseData"
                ),
            )
            self.assertTrue(
                os.path.samefile(
                    os.path.join(self.dataset_dir, "BaseData"),
                    os.path.join(
                        os.path.dirname(os.path.dirname(scenario_dir)), "BaseData"
                    ),
                )
            )

            with open(
                simccs_helper.get_sources_file(scenario_dir), "r"
            ) as sources_file:
                self.assertEqual(sources_file.read(), self.sources)

            with open(simccs_helper.get_sinks_file(scenario_dir), "r") as sinks_file:
                self.assertEqual(sinks_file.read(), self.sinks)

    def test_write_mps_file(self):

        with tempfile.TemporaryDirectory() as datasets_basepath:

            scenario_dir = simccs_helper.create_scenario_dir(
                datasets_basepath,
                self.dataset_dir,
                self.sources,
                self.sinks,
                candidate_network=self.candidate_network)
            simccs_helper.write_mps_file(
                scenario_dir, capital_recovery_rate=0.2, num_years=12, capacity_target=7
            )

            with open(simccs_helper.get_mps_file(scenario_dir), "r") as f:
                contents = f.read()
                # Make sure input parameters are written into the file
                self.assertIn("captureTarget	H1	1.0", contents)
                self.assertIn("rhs	H1	7.0", contents)
                self.assertIn("crf	H2	1.0", contents)
                self.assertIn("rhs	H2	0.2", contents)
                self.assertIn("projectLength	H3	1.0", contents)
                self.assertIn("rhs	H3	12.0", contents)

    def test_load_solution(self):

        with tempfile.TemporaryDirectory() as datasets_basepath:

            scenario_dir = simccs_helper.create_scenario_dir(
                datasets_basepath,
                self.dataset_dir,
                self.sources,
                self.sinks,
                solution=self.solution,
                mps=self.mps,
                candidate_network=self.candidate_network
            )
            solution = simccs_helper.load_solution(scenario_dir)
            self.assertEqual(4, solution.numOpenedSources)
            self.assertEqual(3, solution.numOpenedSinks)
            self.assertEqual(1500, solution.captureAmount)
            self.assertEqual(26, solution.numEdgesOpened)
            self.assertEqual(30, solution.projectLength)
            self.assertAlmostEqual(4669.04, solution.totalAnnualCaptureCost, places=2)
            self.assertAlmostEqual(93.38, solution.unitCaptureCost, places=2)
            self.assertAlmostEqual(127.70, solution.totalAnnualTransportCost, places=2)
            self.assertAlmostEqual(2.55, solution.unitTransportCost, places=2)
            self.assertAlmostEqual(192.87, solution.totalAnnualStorageCost, places=2)
            self.assertAlmostEqual(3.86, solution.unitStorageCost, places=2)
            self.assertAlmostEqual(4989.62, solution.totalCost, places=2)
            self.assertAlmostEqual(99.79, solution.unitTotalCost, places=2)
            self.assertAlmostEqual(0.1, solution.getCRF(), places=2)
