import unittest

import numpy as np

from iso12354_engine import (
    OCTAVE,
    THIRD_OCTAVE,
    airborne_detailed,
    double_roof_rain_spectrum,
    facade_detailed,
    impact_detailed,
    outdoor_sound_power_detailed,
    rain_excitation,
    rainfall_indoor_level,
    rainfall_material_spectrum,
    room_absorption_detailed,
    service_equipment_detailed,
)


class Iso12354EngineTests(unittest.TestCase):
    def test_part1_exposes_dd_df_fd_ff_and_energetic_penalty(self):
        direct = np.full_like(THIRD_OCTAVE, 50.0)
        result = airborne_detailed(
            direct, THIRD_OCTAVE, 12.0, 36.0,
            junctions=[{
                "name": "T1", "source_curve": direct, "receiver_curve": direct,
                "frequencies": THIRD_OCTAVE, "kij": 10.0, "length": 3.0,
            }],
        )
        self.assertEqual([p["name"].split(" · ")[0] for p in result["paths"]], ["Dd", "Df", "Fd", "Ff"])
        self.assertTrue(np.all(result["apparent_curve"] <= direct))

    def test_part2_floor_improvement_reduces_direct_impact(self):
        base = np.full_like(THIRD_OCTAVE, 75.0)
        improvement = np.full_like(THIRD_OCTAVE, 15.0)
        result = impact_detailed(base, THIRD_OCTAVE, improvement)
        self.assertTrue(np.allclose(result["direct_curve"], 60.0))

    def test_part3_combines_large_small_and_joint_paths(self):
        target = THIRD_OCTAVE[3:]
        result = facade_detailed(
            [{"name": "Wall", "area": 9.0, "curve": np.full_like(target, 50.0), "frequencies": target}],
            35.0, 12.0,
            small_elements=[{"name": "Vent", "dne_curve": np.full_like(target, 35.0), "frequencies": target}],
            joints=[{"name": "Joint", "rs_curve": np.full_like(target, 45.0), "frequencies": target, "length": 4.0}],
        )
        self.assertEqual(len(result["paths"]), 3)
        self.assertTrue(np.all(np.isfinite(result["d2mnt_curve"])))

    def test_part4_sums_radiated_elements(self):
        target = THIRD_OCTAVE[3:]
        result = outdoor_sound_power_detailed(
            np.full_like(target, 70.0), target,
            [{"name": "Wall", "area": 10.0, "curve": np.full_like(target, 40.0), "frequencies": target}],
        )
        self.assertTrue(np.allclose(result["sound_power_curve"], 34.0))
        self.assertTrue(np.isfinite(result["lwa"]))

    def test_part5_sums_air_duct_and_structure_paths(self):
        paths = [
            {"name": "Air", "kind": "airborne_same_room", "source_curve": np.full_like(OCTAVE, 60.0), "frequencies": OCTAVE},
            {"name": "Duct", "kind": "duct_outlet", "source_curve": np.full_like(OCTAVE, 55.0), "frequencies": OCTAVE},
            {"name": "Structure", "kind": "structure_borne", "source_curve": np.full_like(OCTAVE, 80.0), "transfer_curve": np.full_like(OCTAVE, -30.0), "frequencies": OCTAVE},
        ]
        result = service_equipment_detailed(paths, 20.0)
        self.assertEqual(len(result["paths"]), 3)
        self.assertTrue(np.all(np.isfinite(result["normalized_curve"])))

    def test_part6_sabine_known_case(self):
        result = room_absorption_detailed(
            100.0,
            [{"name": "All", "area": 100.0, "alpha": [0.2] * 6, "frequencies": [125, 250, 500, 1000, 2000, 4000]}],
        )
        self.assertTrue(np.allclose(result["reverberation_time"], 0.805))

    def test_rain_trace_and_mam_are_exposed(self):
        excitation = rain_excitation(40.0, 3.0, area_m2=20.0)
        self.assertGreater(excitation["drops_per_second"], 0.0)
        outer = rainfall_material_spectrum(
            7850.0, 0.0008, 200e9, 0.30, 0.01, 40.0,
            roof_area=20.0, drop_diameter_mm=3.0,
        )
        self.assertTrue(np.allclose(outer["sound_power_curve"] - outer["li_curve"], 10.0 * np.log10(20.0)))
        double = double_roof_rain_spectrum(outer, 735.0, 0.013, 0.15, 2.5e9)
        indoor = rainfall_indoor_level(double["li_curve"], double["frequencies"], 20.0, 60.0, 0.6)
        self.assertGreater(double["mam_frequency"], 0.0)
        self.assertIn("calcISPLTwoPort", double["calculation_trace"])
        self.assertTrue(np.isfinite(indoor["la_indoor"]))


if __name__ == "__main__":
    unittest.main()
