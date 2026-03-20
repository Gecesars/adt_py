import unittest
import xml.etree.ElementTree as ET

from catalogs import CableCatalog
from tests.helpers import PROJECT_ROOT


class CableCatalogTests(unittest.TestCase):
    def test_catalog_defaults_to_project_local_xml_copy(self):
        catalog = CableCatalog()

        self.assertEqual(
            catalog.xml_path,
            PROJECT_ROOT / "assets" / "original_adt" / "Rating" / "CableRating.xml",
        )
        self.assertTrue(catalog.xml_path.exists())

    def test_catalog_loads_feeder_names_from_project_xml(self):
        catalog = CableCatalog(PROJECT_ROOT / "assets" / "original_adt" / "Rating" / "CableRating.xml")

        self.assertIn("HCA38-50", catalog.feeder_names)
        self.assertGreater(len(catalog.feeder_names), 5)
        self.assertEqual(catalog.default_feeder_name, "HCA38-50")

    def test_feeder_loss_matches_legacy_nearest_sample_logic(self):
        xml_path = PROJECT_ROOT / "assets" / "original_adt" / "Rating" / "CableRating.xml"
        catalog = CableCatalog(xml_path)
        frequency_mhz = 539.0
        length_m = 100.0

        tree = ET.parse(xml_path)
        root = tree.getroot()
        nearest_point = min(
            (
                cable
                for cable in root.findall("Cable")
                if cable.findtext("Name", default="") == "HCA38-50"
            ),
            key=lambda cable: abs(
                float(cable.findtext("Frequency", default="0")) - frequency_mhz
            ),
        )
        expected_loss = float(
            nearest_point.findtext("AttenuationdBm", default="0")
        ) * length_m / 100.0

        actual_loss = catalog.calculate_feeder_loss_db(
            "HCA38-50",
            length_m,
            frequency_mhz,
        )

        self.assertAlmostEqual(actual_loss, expected_loss, places=9)


if __name__ == "__main__":
    unittest.main()
