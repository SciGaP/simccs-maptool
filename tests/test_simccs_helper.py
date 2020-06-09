import os
import tempfile
import unittest

from simccs_maptool import datasets, simccs_helper

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

os.environ["DJANGO_SETTINGS_MODULE"] = "tests.test_settings"

SOURCES = """ID	costFix ($M)	fixO&M ($M/y)	varO&M ($/tCO2)	capMax (MtCO2/y)	N/A	LON	LAT	NAME
1	2842.8	223.4	81.93	7.236	1	-88.0103	31.0069	1
2	3052.4	234.5	58	7.236	1	-86.4567	33.2442	2
3	407.9	52.5	106.78	0.297	1	-85.9708	34.0128	3
4	2108.5	192	71.9	4.635	1	-87.2003	33.6446	4
5	904.4	80.1	67.06	2.034	1	-87.7811	32.6017	5
6	3959	258.9	36.12	17.901	1	-87.0597	33.6319	6
7	1910.5	160.8	94.74	3.276	1	-87.2289	30.5661	7
8	539.6	62.9	88.11	1.26	1	-85.7003	30.2689	8
9	339.6	48.6	123.82	0.018	1	-84.8869	30.6689	9
10	4535	288.8	79.8	17.928	1	-84.9192	34.1256	10
11	1424	141.5	69.03	3.096	1	-85.3456	34.2533	11
12	2361	190.6	77.67	5.319	1	-83.2994	33.1942	12
13	834.4	78.4	83.98	1.782	1	-84.475	33.8244	13
14	474.6	73.3	93.05	1.026	1	-81.1458	32.1486	14
15	264.7	31.1	81.24	0.027	1	-84.1322	31.4444	15
16	5295	311.2	41.91	20.331	1	-83.8072	33.0583	16
17	2539	155.1	67.62	6.129	1	-85.0345	33.4124	17
18	2307.4	239.4	72.62	4.059	1	-84.8986	33.4622	18
19	1405.6	102.3	68.72	2.529	1	-89.0265	30.4408	19
20	2091	128.6	89.68	5.013	1	-88.5574	30.5335	20
"""

SINKS = """0	1	2	3	4	5	6	7	8	9	10	11	12	13	14	15	16
1	1	379	40.951	0.000	0.375	4.575	0.175	2.61	0	-91.2980	28.9920	0	0	0	0	Gulf offshore
2	2	379	40.951	0.000	0.375	4.575	0.175	2.61	0	-91.1764	31.5559	0	0	0	0	Cranfield
3	3	360	63.063	0.000	0.180	3.859	0.201	3.02	0	-88.5068	30.5078	0	0	0	0	Escatawpa
4	4	498	63.063	0.000	0.500	3.602	0.181	2.84	0	-88.2337	31.0930	0	0	0	0	Citronelle
5	5	480	18.178	0.000	0.500	4.204	0.191	2.74	0	-86.7961	30.7153	0	0	0	0	Disposal Area 1 (DA1)
6	6	549	63.063	0.000	0.600	3.017	0.154	2.83	0	-84.8449	30.6128	0	0	0	0	Disposal Area 2 (DA1b)
7	7	845	63.063	0.000	0.800	2.930	0.135	2.77	0	-81.6781	31.7306	0	0	0	0	Disposal Area 3 (DA2)
"""


class TestSimCCSHelper(unittest.TestCase):
    def setUp(self):
        dataset_id = datasets.SOUTHEASTUS_DATASET_ID
        self.dataset_dir = datasets.get_dataset_dir(dataset_id)
        with open(
            os.path.join(
                self.dataset_dir, "Scenarios", "scenario1", "Sources", "Sources.txt"
            ),
            "r",
        ) as sources, open(
            os.path.join(
                self.dataset_dir, "Scenarios", "scenario1", "Sinks", "Sinks.txt"
            ),
            "r",
        ) as sinks:
            self.sources = sources.read()
            self.sinks = sinks.read()

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
                datasets_basepath, self.dataset_dir, self.sources, self.sinks
            )
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

        scenario_dir = os.path.join(self.dataset_dir, "Scenarios", "scenario1")
        results_dir = os.path.join(scenario_dir, "Results", "50MTyr")
        solution = simccs_helper.load_solution(scenario_dir, results_dir)
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
