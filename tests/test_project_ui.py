"""Exercise the actual room/matrix UI blocks with isolated in-memory projects."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class ProjectUITests(unittest.TestCase):
    def app(self):
        path = str(Path(__file__).parents[1] / "app.py")
        script = '''
import ast, textwrap, math, secrets, hashlib
from datetime import datetime
from pathlib import Path
from copy import deepcopy
import pandas as pd
import streamlit as st
from descriptor_optimizer import canonical_descriptor as canonical_design_descriptor
source = Path(APP_PATH).read_text()
tree = ast.parse(source)
names = {"project_rooms", "rename_room", "upsert_room", "requirement_indicators", "compatible_requirement_targets", "validate_custom_requirement", "norm_target_rows", "norm_targets_df", "project_requirements", "upsert_requirement", "make_requirement_id", "requirement_matrix_dataframe", "solution_status", "solution_descriptor_value", "sonara_select_report_solutions"}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), "functions", "exec"))
st.session_state.setdefault("db", {"p": {"tipo": "Vivienda", "norma": "Todas", "recintos": [{"id": "one", "nombre": "Emisor", "area": 20.4, "volumen": 51}, {"id": "two", "nombre": "Receptor", "area": 11.5, "volumen": 28.8}], "requerimientos": []}})
def load_projects(): return deepcopy(st.session_state["db"])
def save_projects(value): st.session_state["db"] = deepcopy(value)
def active_project(): return "p", load_projects()["p"]
df_targets = norm_targets_df()
tab_recintos, tab_matriz = st.tabs(["Recintos", "Elementos"])
block = source[source.index("    # 2. Recintos\\n", source.index("def app_proyectos")):source.index("    # 4. Diseñar\\n", source.index("def app_proyectos"))]
exec(textwrap.dedent(block))
'''.replace("APP_PATH", repr(path))
        return AppTest.from_string(script, default_timeout=15).run()

    def test_empty_facade_catalog_and_custom_save(self):
        app = self.app()
        self.assertFalse(app.exception)
        app.selectbox(key="matrix_tipo").select("Fachada").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.button(key="matrix_add").disabled)
        app.radio(key="matrix_requirement_origin").set_value("Personalizado").run()
        app.text_input(key="matrix_custom_name").set_value("FA-01 · Fachada norte")
        app.number_input(key="matrix_custom_limit_Fachada_D2m,nT,w").set_value(40)
        app.text_area(key="matrix_custom_source").set_value("Objetivo académico de prueba")
        app.run()
        app.button(key="matrix_add").click().run()
        self.assertFalse(app.exception)
        req = app.session_state["db"]["p"]["requerimientos"][0]
        self.assertEqual(req["indicador"], "D2m,nT,w")
        self.assertEqual(req["valor"], 40)
        self.assertEqual(req["origen"], "personalizado")

    def test_decimal_limit_is_preserved(self):
        app = self.app()
        app.selectbox(key="matrix_tipo").select("Reverberación").run()
        app.radio(key="matrix_requirement_origin").set_value("Personalizado").run()
        app.text_input(key="matrix_custom_name").set_value("TR de diseño")
        app.number_input(key="matrix_custom_limit_Reverberación_T").set_value(0.6)
        app.text_area(key="matrix_custom_source").set_value("Criterio de prueba")
        app.run()
        app.button(key="matrix_add").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["db"]["p"]["requerimientos"][0]["valor"], 0.6)

    def test_installation_custom_and_rename(self):
        app = self.app()
        app.selectbox(key="matrix_tipo").select("Instalaciones / HVAC").run()
        self.assertTrue(app.button(key="matrix_add").disabled)
        app.radio(key="matrix_requirement_origin").set_value("Personalizado").run()
        app.text_input(key="matrix_custom_name").set_value("IN-01 · Sanitaria")
        app.number_input(key="matrix_custom_limit_Instalaciones / HVAC_LAFmax,nT").set_value(30)
        app.text_area(key="matrix_custom_source").set_value("Máximo normalizado, descarga de prueba")
        app.run()
        app.button(key="matrix_add").click().run()
        req = app.session_state["db"]["p"]["requerimientos"][0]
        self.assertEqual(req["sentido"], "<=")
        app.text_input(key="room_rename_name").set_value("Estar A-301")
        app.button(key="room_rename_save").click().run()
        self.assertFalse(app.exception)
        project = app.session_state["db"]["p"]
        self.assertEqual(project["recintos"][0]["id"], "one")
        self.assertEqual(project["recintos"][0]["nombre"], "Estar A-301")
        self.assertEqual(project["requerimientos"][0]["recinto_emisor"], "Estar A-301")


if __name__ == "__main__":
    unittest.main()
