import unittest

from simccs_maptool import serializers


class TestDatasetSerializer(unittest.TestCase):
    def test_map_column_names(self):
        serializer = serializers.DatasetSerializer()
        self.assertEqual("costFix ($M)", serializer._map_column_names("costfix"))
        self.assertEqual("costFix ($M)", serializer._map_column_names("costFix"))
        self.assertEqual("costFix ($M)", serializer._map_column_names("costFix $M"))
        self.assertEqual("fixO&M ($M/y)", serializer._map_column_names("fixo&m"))
        self.assertEqual("fixO&M ($M/y)", serializer._map_column_names("fixom"))
        self.assertEqual("varO&M ($/tCO2)", serializer._map_column_names("varo&m"))
        self.assertEqual("varO&M ($/tCO2)", serializer._map_column_names("varom"))
        self.assertEqual("capMax (MtCO2/y)", serializer._map_column_names("capmax"))
        self.assertEqual("LON", serializer._map_column_names("lon"))
        self.assertEqual("LAT", serializer._map_column_names("lat"))
        self.assertEqual("ID", serializer._map_column_names("id"))
        self.assertEqual("Sink_ID", serializer._map_column_names("sink_id"))
        self.assertEqual("fieldCap (MtCO2)", serializer._map_column_names("fieldcap"))
        self.assertEqual("wellCap (MtCO2/yr)", serializer._map_column_names("wellcap"))
        self.assertEqual("wellCostFix ($M)",
                         serializer._map_column_names("wellcostfix"))
        self.assertEqual("wellFixO&M ($M/yr)",
                         serializer._map_column_names("wellfixo&m"))
        self.assertEqual("wellFixO&M ($M/yr)",
                         serializer._map_column_names("wellfixom"))
