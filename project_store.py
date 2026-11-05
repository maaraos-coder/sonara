"""Private cloud persistence; client is a server-only Supabase service client.

SONARA authenticates accounts server-side rather than through Supabase Auth.
The caller must derive the owner from that verified session, never a form field.
The public roles have no access to these tables or to the save RPC.
"""
from copy import deepcopy
import json


class ProjectStorageError(RuntimeError):
    pass


class ProjectConflictError(ProjectStorageError):
    pass


def account_owner(session):
    email = str(session.get("email", "")).strip().lower()
    if not email or "@" not in email or not session.get("license_info", {}).get("allowed"):
        raise ProjectStorageError("Debes iniciar sesión para acceder a tus proyectos.")
    return email


class CloudProjectStore:
    def __init__(self, client, session):
        self.owner = account_owner(session)
        if client is None:
            raise ProjectStorageError("No está disponible la conexión con Supabase.")
        self.client = client

    def load(self):
        try:
            rows = self.client.table("sonara_project_documents").select("payload,revision,updated_at").eq("owner_email", self.owner).limit(1).execute().data or []
            if not rows:
                return {}, 0
            row = rows[0]
            if not isinstance(row.get("payload"), dict) or int(row["revision"]) < 1:
                raise ValueError("Invalid cloud document")
            return deepcopy(row["payload"]), int(row["revision"])
        except Exception as exc:
            raise ProjectStorageError("No se pudieron recuperar tus proyectos de Supabase. No se usará una copia vacía ni local para sustituirlos.") from exc

    def save(self, projects, expected_revision):
        if not isinstance(projects, dict):
            raise ProjectStorageError("El archivo de proyectos no es válido.")
        # Fail before sending invalid/non-finite values to JSONB.
        try:
            payload = json.loads(json.dumps(projects, ensure_ascii=False, allow_nan=False))
            response = self.client.rpc("sonara_save_project_document", {
                "p_owner_email": self.owner,
                "p_payload": payload,
                "p_expected_revision": int(expected_revision),
            }).execute()
            revision = int(response.data)
            if revision < 1:
                raise ValueError("Invalid saved revision")
            return revision
        except Exception as exc:
            if "SONARA_REVISION_CONFLICT" in str(exc):
                raise ProjectConflictError("Otra sesión actualizó tus proyectos. Descarga tus cambios pendientes y vuelve a cargar antes de guardar.") from exc
            raise ProjectStorageError("No se confirmó el guardado en Supabase. Tus cambios no deben considerarse guardados.") from exc

    def versions(self):
        try:
            return self.client.table("sonara_project_versions").select("revision,created_at").eq("owner_email", self.owner).order("revision", desc=True).limit(50).execute().data or []
        except Exception as exc:
            raise ProjectStorageError("No se pudo recuperar el historial de versiones.") from exc

    def version(self, revision):
        try:
            rows = self.client.table("sonara_project_versions").select("payload").eq("owner_email", self.owner).eq("revision", int(revision)).limit(1).execute().data or []
            if not rows or not isinstance(rows[0].get("payload"), dict):
                raise ValueError("Version not found")
            return deepcopy(rows[0]["payload"])
        except Exception as exc:
            raise ProjectStorageError("No se pudo recuperar esa versión.") from exc
