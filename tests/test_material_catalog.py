import unittest
import re

import numpy as np

from material_catalog import (
    absorption_catalog,
    absorption_properties,
    browse_catalog,
    calculation_materials,
    catalog_available,
    catalog_database_path,
    catalog_summary,
    connection_catalog,
    connection_properties,
    floor_cover_catalog,
    floor_cover_spectrum,
    porous_absorption_spectrum,
)


class MaterialCatalogTests(unittest.TestCase):
    def test_catalogue_assets_and_counts(self):
        self.assertTrue(catalog_available())
        self.assertTrue(catalog_database_path().exists())
        summary = dict(zip(catalog_summary()["dataset"], catalog_summary()["records"]))
        self.assertEqual(summary["Materials"], 1547)
        self.assertEqual(summary["Glazing"], 81)
        self.assertEqual(sum(summary.values()), 3515)

    def test_only_complete_isotropic_records_enter_plate_calculation(self):
        materials = calculation_materials()
        self.assertEqual(len(materials), 1229)
        for material in list(materials.values())[:25]:
            self.assertEqual(material["model_type"], "Isotropic")
            self.assertGreater(material["dens"], 0.0)
            self.assertGreater(material["E"], 0.0)
            self.assertGreater(material["espesor"], 0.0)

    def test_catalogue_has_no_cjk_identity_labels(self):
        cjk = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
        frame = browse_catalog(limit=5000)
        labels = frame["name"].fillna("") + " " + frame["manufacturer"].fillna("")
        self.assertFalse(labels.str.contains(cjk).any())

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

    def test_absorption_catalogue_exposes_physical_estimates(self):
        absorbers = absorption_catalog()
        self.assertGreaterEqual(len(absorbers), 400)
        entity_id = int(absorbers.iloc[0]["entity_id"])
        properties = absorption_properties(entity_id)
        self.assertGreater(properties["flow_resistivity_pa_s_m2"], 0.0)
        spectrum = porous_absorption_spectrum(
            entity_id, np.array([125, 250, 500, 1000, 2000, 4000], dtype=float)
        )
        self.assertTrue(np.all(np.isfinite(spectrum.to_numpy())))
        self.assertTrue(np.all((spectrum.to_numpy() >= 0.0) & (spectrum.to_numpy() < 1.0)))

    def test_connection_catalogue_exposes_structural_geometry(self):
        connections = connection_catalog()
        self.assertGreaterEqual(len(connections), 300)
        entity_id = int(connections.iloc[0]["entity_id"])
        properties = connection_properties(entity_id)
        self.assertGreater(properties["stud_depth_m"], 0.0)
        self.assertGreater(properties["defined_stud_spacing_m"], 0.0)


if __name__ == "__main__":
    unittest.main()

