import unittest

import numpy as np

from iso_design import (
    AIRBORNE_REFERENCE,
    IMPACT_REFERENCE,
    THIRD_OCTAVE_100_3150,
    airborne_rating,
    airborne_single_numbers,
    compare_predicted_measured,
    dnt_from_apparent_curve,
    facade_single_numbers,
    facade_spectral_prediction,
    impact_rating,
    manual_airborne_curve,
    reverberation_prediction,
    service_equipment_airborne,
    transmission_average_db,
)


class IsoDesignTests(unittest.TestCase):
    def test_transmission_average_preserves_constant_curve(self):
        self.assertAlmostEqual(transmission_average_db([42.0, 42.0, 42.0]), 42.0)

    def test_airborne_rating_accepts_32_db_deviation_limit(self):
        rating, _, _ = airborne_rating(
            THIRD_OCTAVE_100_3150, AIRBORNE_REFERENCE - 7.0
        )
        self.assertEqual(rating, 47)

    def test_standardized_level_difference_conversion(self):
        value = dnt_from_apparent_curve([50.0], volume=35.0, separating_area=10.0)
        self.assertAlmostEqual(float(value[0]), 50.49218023, places=6)

    def test_impact_curve_fitting_and_ci(self):
        result = impact_rating(THIRD_OCTAVE_100_3150, IMPACT_REFERENCE)
        self.assertEqual(result["weighted"], 58)
        self.assertEqual(result["ci"], -1)
        self.assertIsNone(result["ci50_2500"])

    def test_facade_combines_opaque_and_glazed_areas(self):
        result = facade_single_numbers(
            [
                {"area": 9, "rw": 50, "ctr": -5},
                {"area": 3, "rw": 32, "ctr": -6},
            ],
            volume=35,
            facade_area=12,
            lden=65,
        )
        self.assertAlmostEqual(result["rw_composite"], 37.8189, places=3)
        self.assertAlmostEqual(result["dnt_a_tr"], 31.5600, places=3)
        self.assertAlmostEqual(result["indoor_from_lden"], 33.4400, places=3)

    def test_facade_spectral_prediction_combines_transmission_factors(self):
        opaque = np.full_like(THIRD_OCTAVE_100_3150, 50.0, dtype=float)
        window = np.full_like(THIRD_OCTAVE_100_3150, 30.0, dtype=float)
        result = facade_spectral_prediction(
            [
                {"area": 9.0, "freqs": THIRD_OCTAVE_100_3150, "curve": opaque},
                {"area": 3.0, "freqs": THIRD_OCTAVE_100_3150, "curve": window},
            ],
            volume=35.0,
            facade_area=12.0,
            lden=65.0,
        )
        expected_curve = -10.0 * np.log10((9.0 * 10.0 ** -5 + 3.0 * 10.0 ** -3) / 12.0)
        self.assertTrue(np.allclose(result["curve"], expected_curve))
        self.assertAlmostEqual(
            result["indoor_from_lden"], 65.0 - result["dnt_a_tr"], places=9
        )

    def test_manual_facade_curve_preserves_requested_rw(self):
        curve = manual_airborne_curve(42.0, -6.0)
        result = airborne_single_numbers(THIRD_OCTAVE_100_3150, curve)
        self.assertEqual(result["weighted"], 42)
        self.assertEqual(result["ctr"], -6)

    def test_equipment_same_room_returns_seven_finite_bands(self):
        result = service_equipment_airborne(
            [70, 68, 66, 64, 61, 58, 55], 2, 2, 20, 20
        )
        self.assertEqual(len(result["lp_normalized"]), 7)
        self.assertTrue(np.all(np.isfinite(result["lp_normalized"])))
        self.assertAlmostEqual(result["la_normalized"], 60.2520, places=3)

    def test_sabine_reverberation_known_case(self):
        result = reverberation_prediction(
            100,
            50,
            [{"area": 100, "alpha": [0.2] * 6}],
        )
        self.assertTrue(np.allclose(result["reverberation_time"], 0.805))
        self.assertAlmostEqual(result["a_over_sfloor_250_2000"], 0.4)

    def test_measured_prediction_comparison_reports_bias_and_rw(self):
        predicted = AIRBORNE_REFERENCE + 3.0
        measured = predicted - 2.0
        result = compare_predicted_measured(
            THIRD_OCTAVE_100_3150, predicted,
            THIRD_OCTAVE_100_3150, measured,
        )
        self.assertAlmostEqual(result["bias"], 2.0)
        self.assertAlmostEqual(result["mae"], 2.0)
        self.assertAlmostEqual(result["rmse"], 2.0)
        self.assertEqual(result["delta_rw"], 2)

    def test_measured_prediction_comparison_rejects_duplicate_bands(self):
        with self.assertRaises(ValueError):
            compare_predicted_measured([100, 200], [20, 30], [100, 100], [19, 20])


if __name__ == "__main__":
    unittest.main()
