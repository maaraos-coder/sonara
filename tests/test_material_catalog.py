import unittest

import numpy as np

from material_catalog import (
    browse_catalog,
    calculation_materials,
    catalog_available,
    catalog_database_path,
    catalog_summary,
    floor_cover_catalog,
    floor_cover_spectrum,
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

    def test_floor_cover_catalogue_exposes_measured_isolation_gain(self):
        covers = floor_cover_catalog()
        self.assertEqual(len(covers), 674)
        frequencies = np.array([100, 125, 160, 200, 250, 315, 400, 500,
                                630, 800, 1000, 1250, 1600, 2000, 2500,
                                3150], dtype=float)
        spectrum = floor_cover_spectrum(int(covers.iloc[0]["entity_id"]), frequencies)
        self.assertEqual(len(spectrum), len(frequencies))
        self.assertTrue(np.all(np.isfinite(spectrum.to_numpy())))


if __name__ == "__main__":
    unittest.main()

