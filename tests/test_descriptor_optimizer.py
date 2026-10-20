import unittest

from descriptor_optimizer import (
    canonical_descriptor, default_direction, descriptor_family,
    descriptor_value, evaluate, rank_solutions,
)


class DescriptorOptimizerTests(unittest.TestCase):
    def test_aliases_and_direction_cover_residential_descriptors(self):
        self.assertEqual(canonical_descriptor("D₂m,nT,w"), "d2mntw")
        self.assertEqual(canonical_descriptor("L′nT,w"), "lntw")
        self.assertEqual(descriptor_family("LAeq,nT"), "Instalaciones")
        self.assertEqual(default_direction("DₙT,w"), ">=")
        self.assertEqual(default_direction("L′nT,w"), "<=")


    def test_extracts_values_from_each_calculation_family(self):
        self.assertEqual(descriptor_value({"dntw": 53}, "DnT,w"), 53)
        self.assertEqual(descriptor_value({"lntw": 48}, "L'nT,w"), 48)
        self.assertEqual(descriptor_value({"tipo_calculo": "Fachada ISO 12354-3", "valor": 39}, "D2m,nT,Atr"), 39)
        self.assertEqual(descriptor_value({"tipo_calculo": "Ruido de instalaciones EN 12354-5", "valor": 31}, "LAeq,nT"), 31)


    def test_margin_is_always_positive_in_favourable_direction(self):
        self.assertEqual(evaluate(54, 50, ">=").margin, 4)
        self.assertEqual(evaluate(46, 50, "<=").margin, 4)
        self.assertEqual(evaluate(52, 50, "<=").margin, -2)


    def test_ranking_respects_lower_is_better_for_impact(self):
        solutions = [
            {"nombre": "Base", "lntw": 55, "costo": 0},
            {"nombre": "A", "lntw": 47, "costo": 20},
            {"nombre": "B", "lntw": 45, "costo": 30},
        ]
        ranked = rank_solutions(solutions, "L'nT,w", 50, "<=", "Mayor desempeño")
        self.assertEqual([row["name"] for row in ranked], ["B", "A", "Base"])
        self.assertTrue(ranked[0]["complies"])


if __name__ == "__main__":
    unittest.main()
