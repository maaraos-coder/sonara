"""Project regressions without executing Streamlit's top-level application."""
import ast
from copy import deepcopy
from datetime import datetime
import math
from pathlib import Path
import secrets
from types import SimpleNamespace
import unittest

import pandas as pd
from descriptor_optimizer import canonical_descriptor


class ProjectRequirementsTests(unittest.TestCase):
    def setUp(self):
        names = {"project_rooms", "rename_room", "upsert_room", "requirement_indicators", "compatible_requirement_targets", "validate_custom_requirement", "solution_descriptor_value", "solution_status", "norm_target_rows"}
        tree = ast.parse((Path(__file__).parents[1] / "app.py").read_text())
        self.db = {"p": {"recintos": [{"id": "stable", "nombre": "Estar antiguo", "area": 20.4, "volumen": 51}], "requerimientos": [{"id": "req1", "recinto_emisor": "Estar antiguo", "recinto_receptor": "Dormitorio", "soluciones": [{"id": "sol1", "objetivo": {"recinto_emisor": "Estar antiguo"}}]}]}}
        self.state = {"matrix_emisor": "Estar antiguo", "active_requirement": {"recinto_receptor": "Estar antiguo"}}
        self.saved = []
        def save(value):
            self.db = deepcopy(value)
            self.saved.append(deepcopy(value))
        self.env = dict(datetime=datetime, math=math, secrets=secrets, canonical_design_descriptor=canonical_descriptor, st=SimpleNamespace(session_state=self.state), load_projects=lambda: deepcopy(self.db), save_projects=save)
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), "app-functions", "exec"), self.env)

    def test_rename_preserves_ids_solutions_and_updates_nested_links(self):
        self.env["rename_room"]("p", "stable", "Estar A-301")
        p = self.db["p"]
        self.assertEqual(p["recintos"][0], {"id": "stable", "nombre": "Estar A-301", "area": 20.4, "volumen": 51})
        r = p["requerimientos"][0]
        self.assertEqual(r["id"], "req1")
        self.assertEqual(r["recinto_emisor"], "Estar A-301")
        self.assertEqual(r["soluciones"][0]["objetivo"]["recinto_emisor"], "Estar A-301")
        self.assertEqual(self.state["active_requirement"]["recinto_receptor"], "Estar A-301")
        self.assertNotIn("matrix_emisor", self.state)

    def test_rename_rejects_empty_duplicate_and_missing_without_writes(self):
        self.db["p"]["recintos"].append({"id": "other", "nombre": "Dormitorio"})
        for rid, name in [("stable", "  "), ("stable", " dormitorio "), ("missing", "Nuevo")]:
            with self.assertRaises(ValueError):
                self.env["rename_room"]("p", rid, name)
        self.assertEqual(self.saved, [])

    def test_updating_renamed_room_keeps_stable_id(self):
        self.env["rename_room"]("p", "stable", "Estar A-301")
        self.env["upsert_room"]("p", {"nombre": "Estar A-301", "area": 21, "volumen": 52.5})
        self.assertEqual(len(self.db["p"]["recintos"]), 1)
        self.assertEqual(self.db["p"]["recintos"][0]["id"], "stable")

    def test_new_room_does_not_overwrite_old_id_after_rename(self):
        self.db["p"]["recintos"][0]["id"] = "room_estar_antiguo"
        self.env["rename_room"]("p", "room_estar_antiguo", "Nuevo")
        self.env["upsert_room"]("p", {"nombre": "Estar antiguo", "area": 1, "volumen": 2})
        self.assertEqual(len(self.db["p"]["recintos"]), 2)
        self.assertEqual(len({r["id"] for r in self.db["p"]["recintos"]}), 2)

    def test_facade_and_installations_never_fall_back_to_unrelated_targets(self):
        frame = pd.DataFrame(self.env["norm_target_rows"]())
        residential = frame[frame.sector == "Vivienda"]
        for kind in ("Fachada", "Instalaciones / HVAC"):
            self.assertTrue(self.env["compatible_requirement_targets"](residential, kind).empty)
        mixed = pd.DataFrame({"indicador": ["Rw", "LAFmax,nT", "LAeq,nT", "D2m,nT,w", "D2m,nT,Atr"]})
        self.assertEqual(len(self.env["compatible_requirement_targets"](mixed, "Fachada")), 2)
        self.assertEqual(len(self.env["compatible_requirement_targets"](mixed, "Instalaciones / HVAC")), 2)

    def test_custom_requires_traceable_finite_limit(self):
        req = dict(elemento="FA-01", indicador="D2m,nT,Atr", valor=38, sentido=">=", unidad="dB", fuente="Criterio académico documentado")
        self.assertEqual(self.env["validate_custom_requirement"](req), req)
        for change in ({"fuente": " "}, {"indicador": ""}, {"valor": math.nan}, {"valor": math.inf}, {"sentido": "="}):
            with self.assertRaises(ValueError):
                self.env["validate_custom_requirement"]({**req, **change})

    def test_no_false_compliance_from_other_descriptor(self):
        status = self.env["solution_status"]
        self.assertEqual(status({"rw": 65, "valor": 65}, {"indicador": "DnT,50", "valor": 58, "sentido": ">="})[0], "Sin evaluación")
        self.assertEqual(status({"laeq_nt": 25}, {"indicador": "LAFmax,nT", "valor": 30, "sentido": "<="})[0], "Sin evaluación")
        self.assertEqual(status({"dntw": 50}, {"indicador": "D2m,nT,w", "valor": 40, "sentido": ">="})[0], "Sin evaluación")
        self.assertEqual(status({"descriptores": {"D2m,nT,w": 45}}, {"indicador": "D2m,nT,w", "valor": 40, "sentido": ">="})[0], "Cumple")


if __name__ == "__main__":
    unittest.main()
