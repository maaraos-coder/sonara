from copy import deepcopy
from types import SimpleNamespace
import ast
from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest

from project_store import CloudProjectStore, ProjectStorageError, ProjectConflictError


class Query:
    def __init__(self, client, table):
        self.client, self.table_name, self.filters = client, table, {}
    def select(self, fields):
        self.fields = fields
        return self
    def eq(self, key, value):
        self.filters[key] = value
        return self
    def limit(self, count):
        return self
    def order(self, *args, **kwargs):
        return self
    def range(self, *args):
        return self
    def execute(self):
        self.client.calls.append((self.table_name, self.filters.copy()))
        if self.client.offline:
            raise RuntimeError("offline")
        return SimpleNamespace(data=[deepcopy(r) for r in self.client.rows[self.table_name] if all(r.get(k) == v for k, v in self.filters.items())])


class Client:
    def __init__(self):
        self.offline = False
        self.calls = []
        self.rows = {"sonara_project_documents": [], "sonara_project_versions": [], "sonara_accounts": [{"email": "a@test.com"}, {"email": "b@test.com"}]}
    def table(self, name):
        return Query(self, name)
    def rpc(self, name, params):
        assert name == "sonara_save_project_document"
        def execute():
            if self.offline:
                raise RuntimeError("offline")
            owner = params["p_owner_email"]
            row = next((r for r in self.rows["sonara_project_documents"] if r["owner_email"] == owner), None)
            revision = row["revision"] if row else 0
            if revision != params["p_expected_revision"]:
                raise RuntimeError("SONARA_REVISION_CONFLICT")
            payload = deepcopy(params["p_payload"])
            if row and row["payload"] == payload:
                return SimpleNamespace(data=revision)
            new = dict(owner_email=owner, payload=payload, revision=revision + 1)
            if row:
                row.update(new)
            else:
                self.rows["sonara_project_documents"].append(new)
            self.rows["sonara_project_versions"].append(deepcopy(new))
            return SimpleNamespace(data=revision + 1)
        return SimpleNamespace(execute=execute)


def session(email):
    return {"email": email, "license_info": {"allowed": True}}


class ProjectStoreTests(unittest.TestCase):
    def test_requires_authenticated_session_and_connection(self):
        for state in ({}, {"email": "a@test.com"}, {"email": "a@test.com", "license_info": {"allowed": False}}):
            with self.assertRaises(ProjectStorageError):
                CloudProjectStore(Client(), state)
        with self.assertRaises(ProjectStorageError):
            CloudProjectStore(None, session("a@test.com"))

    def test_saved_project_recovers_in_new_session_and_isolates_accounts(self):
        client = Client()
        a = CloudProjectStore(client, session(" A@test.com "))
        original = {"project": {"recintos": [{"nombre": "Dormitorio"}], "requerimientos": [{"soluciones": [{"id": "saved"}]}]}}
        self.assertEqual(a.save(original, 0), 1)
        recovered, revision = CloudProjectStore(client, session("a@test.com")).load()
        self.assertEqual((recovered, revision), (original, 1))
        other = CloudProjectStore(client, session("b@test.com"))
        self.assertEqual(other.load(), ({}, 0))
        self.assertEqual(other.versions(), [])
        with self.assertRaises(ProjectStorageError):
            other.version(1)
        self.assertTrue(all(filters.get("owner_email") in ("a@test.com", "b@test.com") for _, filters in client.calls))

    def test_conflict_does_not_overwrite_and_history_can_be_recovered(self):
        client = Client()
        store = CloudProjectStore(client, session("a@test.com"))
        store.save({"one": {}}, 0)
        store.save({"one": {"changed": True}}, 1)
        with self.assertRaises(ProjectConflictError):
            store.save({"one": {"stale": True}}, 1)
        self.assertEqual(store.version(1), {"one": {}})
        self.assertEqual(store.load()[0], {"one": {"changed": True}})

    def test_offline_is_error_not_empty_projects_or_success(self):
        client = Client()
        store = CloudProjectStore(client, session("a@test.com"))
        store.save({"saved": {}}, 0)
        client.offline = True
        with self.assertRaises(ProjectStorageError):
            store.load()
        with self.assertRaises(ProjectStorageError):
            store.save({}, 1)
        self.assertEqual(client.rows["sonara_project_documents"][0]["payload"], {"saved": {}})

    def test_repeated_save_is_idempotent_and_invalid_values_rejected(self):
        store = CloudProjectStore(Client(), session("a@test.com"))
        self.assertEqual(store.save({"one": {}}, 0), 1)
        self.assertEqual(store.save({"one": {}}, 1), 1)
        with self.assertRaises(ProjectStorageError):
            store.save({"one": {"value": float("nan")}}, 1)


class ApplicationStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "a_test_com.json"
        self.client = Client()
        self.session = session("a@test.com")
        class Stopped(Exception):
            pass
        self.Stopped = Stopped
        def stop():
            raise Stopped()
        st = SimpleNamespace(session_state=self.session, error=lambda *a, **k: None, download_button=lambda *a, **k: None, stop=stop)
        self.env = dict(st=st, os=SimpleNamespace(getenv=lambda *a: "supabase"), json=json, datetime=datetime, CloudProjectStore=CloudProjectStore, ProjectStorageError=ProjectStorageError, academy_supabase_client=lambda: self.client, current_user_project_file=lambda *a: self.path, _json_default=str)
        tree = ast.parse((Path(__file__).parents[1] / "app.py").read_text())
        names = {"load_projects", "save_projects", "cloud_project_storage_enabled", "project_storage_failure"}
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), "app-storage", "exec"), self.env)

    def test_import_private_file_once_and_recover_cloud_after_local_file_removed(self):
        old = {"local": {"recintos": []}}
        self.path.write_text(json.dumps(old))
        self.assertEqual(self.env["load_projects"](), old)
        self.path.unlink()
        new = {"local": {"recintos": [{"nombre": "updated"}]}}
        self.env["save_projects"](new)
        self.session.pop("project_cloud_revisions")
        self.assertEqual(self.env["load_projects"](), new)
        self.path.write_text(json.dumps(old))
        self.assertEqual(self.env["load_projects"](), new)

    def test_read_error_stops_instead_of_falling_back_to_local_or_empty(self):
        self.path.write_text('{"stale_local": {}}')
        self.client.offline = True
        with self.assertRaises(self.Stopped):
            self.env["load_projects"]()
        self.assertEqual(self.client.rows["sonara_project_documents"], [])

    def test_failed_save_preserves_pending_changes_and_does_not_claim_success(self):
        self.env["load_projects"]()
        self.client.offline = True
        pending = {"unsaved": {}}
        with self.assertRaises(self.Stopped):
            self.env["save_projects"](pending)
        self.assertEqual(self.session["project_unsaved_changes"], pending)
        self.assertNotIn("project_cloud_last_saved", self.session)


class FileMigrationTests(unittest.TestCase):
    def test_inventory_import_and_conflict_never_overwrite_originals(self):
        from scripts.migrate_project_files import migrate
        client = Client()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "a_test_com.json"
            path.write_text('{"saved": {}}')
            self.assertEqual(migrate(directory, client)[0]["status"], "ready_to_import")
            self.assertEqual(migrate(directory, client, True)[0]["status"], "imported_and_verified")
            self.assertEqual(migrate(directory, client, True)[0]["status"], "already_verified")
            path.write_text('{"different": {}}')
            self.assertEqual(migrate(directory, client, True)[0]["status"], "conflict_kept_both")
            self.assertEqual(CloudProjectStore(client, session("a@test.com")).load()[0], {"saved": {}})
            self.assertTrue(path.exists())
            (Path(directory) / "unknown.json").write_text('{"private": {}}')
            self.assertEqual(migrate(directory, client, True)[1]["status"], "unmatched_or_ambiguous_owner")


if __name__ == "__main__":
    unittest.main()
