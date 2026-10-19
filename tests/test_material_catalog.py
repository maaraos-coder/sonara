import unittest

from material_catalog import (
    browse_catalog,
    calculation_materials,
    catalog_available,
    catalog_database_path,
    catalog_summary,
)


class MaterialCatalogTests(unittest.TestCase):
    def test_catalogue_assets_and_counts(self):
        self.assertTrue(catalog_available())
        self.assertTrue(catalog_database_path().exists())
        summary = dict(zip(catalog_summary()["dataset"], catalog_summary()["records"]))
        self.assertEqual(summary["Materials"], 1576)
        self.assertEqual(summary["Glazing"], 81)
        self.assertEqual(sum(summary.values()), 3646)

    def test_only_complete_isotropic_records_enter_plate_calculation(self):
        materials = calculation_materials()
        self.assertEqual(len(materials), 1255)
        for material in list(materials.values())[:25]:
            self.assertEqual(material["model_type"], "Isotropic")
            self.assertGreater(material["dens"], 0.0)
            self.assertGreater(material["E"], 0.0)
            self.assertGreater(material["espesor"], 0.0)

    def test_chile_filter_returns_enabled_records(self):
        frame = browse_catalog(chile_only=True, limit=5000)
        self.assertEqual(len(frame), 831)


if __name__ == "__main__":
    unittest.main()

