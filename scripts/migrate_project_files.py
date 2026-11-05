"""Run on the OLD Render instance before redeploying; never delete local files.

Default is inventory only. --apply imports missing cloud documents; an existing
different cloud document is reported as a conflict, never overwritten.
Requires server-side Supabase env vars already used by academy_access.
Run from the SONARA app directory: python scripts/migrate_project_files.py --apply
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from academy_access import academy_supabase_client
from project_store import CloudProjectStore, ProjectStorageError


def file_owner_id(email):
    safe = "".join(c.lower() if c.isalnum() else "_" for c in email.strip().lower())
    return "_".join(part for part in safe.split("_") if part)


def migrate(directory, client, apply=False):
    if client is None:
        raise ProjectStorageError("Server-side Supabase connection unavailable")
    # Paginate so every account can be matched; never select credentials.
    accounts, offset = [], 0
    while True:
        page = client.table("sonara_accounts").select("email").range(offset, offset + 499).execute().data or []
        accounts.extend(page)
        if len(page) < 500:
            break
        offset += 500
    owners = {}
    for account in accounts:
        email = account["email"]
        owners.setdefault(file_owner_id(email), []).append(email)
    report = []
    for path in sorted(Path(directory).glob("*.json")):
        matches = owners.get(path.stem, [])
        if len(matches) != 1:
            report.append({"file": path.name, "status": "unmatched_or_ambiguous_owner"})
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(payload, dict):
                raise ValueError("Expected project dictionary")
            store = CloudProjectStore(client, {"email": matches[0], "license_info": {"allowed": True}})
            existing, revision = store.load()
            if revision and existing != payload:
                status = "conflict_kept_both"
            elif revision:
                status = "already_verified"
            elif apply:
                store.save(payload, 0)
                verified, _ = store.load()
                if verified != payload:
                    raise ValueError("Cloud verification failed")
                status = "imported_and_verified"
            else:
                status = "ready_to_import"
            report.append({"file": path.name, "projects": len(payload), "status": status})
        except (ProjectStorageError, ValueError, OSError):
            report.append({"file": path.name, "status": "error_original_retained"})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="data/projects")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = migrate(args.directory, academy_supabase_client(), args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if any(r["status"] in ("unmatched_or_ambiguous_owner", "conflict_kept_both", "error_original_retained") for r in result):
        sys.exit(1)
