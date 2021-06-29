import unittest
from functools import partial

import pandas as pd
from simccs_maptool import serializers


class TestDatasetSerializer(unittest.TestCase):
    def test_map_column_names(self):
        serializer = serializers.DatasetSerializer()
        self.assertEqual("costFix ($M)", serializer._map_column_names("costfix", 'source'))
        self.assertEqual("costFix ($M)", serializer._map_column_names("costFix", 'source'))
        self.assertEqual("costFix ($M)", serializer._map_column_names("costFix $M", 'source'))
        self.assertEqual("fixO&M ($M/y)", serializer._map_column_names("fixo&m", 'source'))
        self.assertEqual("fixO&M ($M/y)", serializer._map_column_names("fixom", 'source'))
        # Note: fixO&M is slightly different for sinks: "fixO&M ($M/yr)"
        self.assertEqual("fixO&M ($M/yr)", serializer._map_column_names("fixo&m", 'sink'))
        self.assertEqual("fixO&M ($M/yr)", serializer._map_column_names("fixom", 'sink'))
        self.assertEqual("varO&M ($/tCO2)", serializer._map_column_names("varo&m", 'source'))
        self.assertEqual("varO&M ($/tCO2)", serializer._map_column_names("varom", 'source'))
        self.assertEqual("capMax (MtCO2/y)", serializer._map_column_names("capmax", 'source'))
        self.assertEqual("LON", serializer._map_column_names("lon", 'source'))
        self.assertEqual("LAT", serializer._map_column_names("lat", 'source'))
        self.assertEqual("ID", serializer._map_column_names("id", 'source'))
        self.assertEqual("Sink_ID", serializer._map_column_names("sink_id", 'source'))
        self.assertEqual("fieldCap (MtCO2)", serializer._map_column_names("fieldcap", 'sink'))
        self.assertEqual("wellCap (MtCO2/yr)", serializer._map_column_names("wellcap", 'sink'))
        self.assertEqual("wellCostFix ($M)",
                         serializer._map_column_names("wellcostfix", 'sink'))
        self.assertEqual("wellFixO&M ($M/yr)",
                         serializer._map_column_names("wellfixo&m", 'sink'))
        self.assertEqual("wellFixO&M ($M/yr)",
                         serializer._map_column_names("wellfixom", 'sink'))

    def test_verify_all_columns_exist_empty_dataframe(self):
        serializer = serializers.DatasetSerializer()
        with self.assertRaises(Exception):
            serializer._verify_all_columns_exist(pd.DataFrame(), "source")
        with self.assertRaises(Exception):
            serializer._verify_all_columns_exist(pd.DataFrame(), "sink")

    def test_verify_all_columns_exist_missing_columns(self):
        serializer = serializers.DatasetSerializer()
        with self.assertRaises(Exception):
            serializer._verify_all_columns_exist(
                pd.DataFrame(
                    columns=[
                        'ID',
                        # 'costFix ($M)',
                        'fixO&M ($M/y)',
                        'varO&M ($/tCO2)',
                        'capMax (MtCO2/y)',
                        'N/A',
                        'LON',
                        'LAT',
                        'NAME']),
                "source")
        with self.assertRaises(Exception):
            serializer._verify_all_columns_exist(
                pd.DataFrame(columns=['ID',
                                      'Sink_ID',
                                      'fieldCap (MtCO2)',
                                      'costFix ($M)',
                                      'fixO&M ($M/yr)',
                                      # 'wellCap (MtCO2/yr)',
                                      'wellCostFix ($M)',
                                      'wellFixO&M ($M/yr)',
                                      'varO&M ($/tCO2)',
                                      'LON',
                                      'LAT',
                                      'Name']), "sink")

    def test_verify_all_columns_exist_all_columns(self):

        serializer = serializers.DatasetSerializer()

        df = pd.DataFrame(columns=['ID',
                                   'costFix ($M)',
                                   'fixO&M ($M/y)',
                                   'varO&M ($/tCO2)',
                                   'capMax (MtCO2/y)',
                                   'N/A',
                                   'LON',
                                   'LAT',
                                   'NAME'])
        df.rename(columns=partial(serializer._map_column_names, dataset_type='source'), inplace=True)
        serializer._verify_all_columns_exist(df, "source")
        df = pd.DataFrame(columns=['ID',
                                   'Sink_ID',
                                   'fieldCap (MtCO2)',
                                   'costFix ($M)',
                                   'fixO&M ($M/yr)',
                                   'wellCap (MtCO2/yr)',
                                   'wellCostFix ($M)',
                                   'wellFixO&M ($M/yr)',
                                   'varO&M ($/tCO2)',
                                   'LON',
                                   'LAT',
                                   'Name'])
        df.rename(columns=partial(serializer._map_column_names, dataset_type='sink'), inplace=True)
        serializer._verify_all_columns_exist(df, 'sink')
