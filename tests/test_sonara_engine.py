import unittest

import numpy as np

from sonara_engine import (
    combine_bonded_layers,
    double_leaf_tl,
    mam_resonance_frequencies,
    plate_properties,
    porous_absorption_coefficients,
    single_leaf_tl,
)


GYPSUM = {
    "dens": 735.0,
    "E": 2.55e9,
    "eta": 0.033,
    "poisson": 0.30,
    "espesor": 15.0,
}


class SonaraEngineTests(unittest.TestCase):
    def test_verified_plate_properties(self):
        plate = plate_properties(735.0, 0.015, 2.55e9, 0.30, 0.033)
        self.assertAlmostEqual(plate.surface_mass, 11.025, places=6)
        self.assertAlmostEqual(plate.bending_stiffness, 788.118131868, places=6)
        self.assertGreater(plate.critical_frequency, 2000.0)
        self.assertGreater(plate.shear_stiffness, 0.0)

    def test_single_leaf_returns_finite_spectrum(self):
        freqs = np.array([50, 100, 200, 400, 800, 1600, 3150, 5000], dtype=float)
        curve, plate = single_leaf_tl([{"material": GYPSUM, "espesor": 15.0}], freqs)
        self.assertEqual(curve.shape, freqs.shape)
        self.assertTrue(np.all(np.isfinite(curve)))
        self.assertTrue(np.all(curve >= 0.0))
        self.assertAlmostEqual(plate.surface_mass, 11.025, places=6)

    def test_bonded_layer_loss_is_mass_weighted(self):
        dense = dict(GYPSUM, dens=1000.0, eta=0.05)
        plate = combine_bonded_layers([
            {"material": GYPSUM, "espesor": 10.0},
            {"material": dense, "espesor": 20.0},
        ])
        expected = ((735 * 0.01 * 0.033) + (1000 * 0.02 * 0.05)) / (735 * 0.01 + 1000 * 0.02)
        self.assertAlmostEqual(plate.loss_factor, expected, places=9)

    def test_mam_solver_matches_closed_two_leaf_frequency(self):
        m1, m2, depth = 11.025, 11.025, 0.070
        calculated = mam_resonance_frequencies([m1, m2], [depth])[0]
        expected = (1.0 / (2.0 * np.pi)) * np.sqrt(1.2 * 343.0**2 / depth * (1.0 / m1 + 1.0 / m2))
        self.assertAlmostEqual(calculated, expected, places=9)

    def test_double_leaf_exposes_resonance_and_finite_curve(self):
        freqs = np.array([50, 63, 80, 100, 125, 250, 500, 1000, 2000, 4000], dtype=float)
        layers = [{"material": GYPSUM, "espesor": 15.0}]
        curve, _, _, resonances, upper = double_leaf_tl(
            layers, layers, 70.0, freqs, absorbent="Lana mineral 60 kg/m³"
        )
        self.assertEqual(len(resonances), 1)
        self.assertGreater(resonances[0], 0.0)
        self.assertGreater(upper, resonances[0])
        self.assertTrue(np.all(np.isfinite(curve)))

    def test_porous_absorption_is_bounded_and_frequency_dependent(self):
        frequencies = np.array([125, 250, 500, 1000, 2000, 4000], dtype=float)
        alpha = porous_absorption_coefficients(10000.0, 0.05, frequencies)
        self.assertTrue(np.all(np.isfinite(alpha)))
        self.assertTrue(np.all((alpha >= 0.0) & (alpha < 1.0)))
        self.assertGreater(float(np.max(alpha) - np.min(alpha)), 0.1)

    def test_double_leaf_uses_catalogue_absorber_and_connection(self):
        frequencies = np.array([63, 125, 250, 500, 1000, 2000, 4000], dtype=float)
        layers = [{"material": GYPSUM, "espesor": 15.0}]
        baseline, *_ = double_leaf_tl(layers, layers, 70.0, frequencies)
        detailed, *_ = double_leaf_tl(
            layers,
            layers,
            70.0,
            frequencies,
            absorbent_properties={
                "thickness_m": 0.05,
                "flow_resistivity_pa_s_m2": 10000.0,
            },
            connection_properties={
                "name": "Independent metal frame",
                "category": "MetalFrame",
                "stud_width_m": 0.035,
                "defined_stud_spacing_m": 0.6,
                "attenuation_factor": 2.0,
                "resonant_transmission": 0,
            },
        )
        self.assertTrue(np.all(np.isfinite(detailed)))
        self.assertFalse(np.allclose(baseline, detailed))


if __name__ == "__main__":
    unittest.main()

