# Project persistence and cutover

Projects now use Supabase by default (`SONARA_PROJECT_STORAGE=supabase`).
`local` is an explicit offline/development mode, not an outage fallback.
Accounts continue to authenticate on the Streamlit server. The storage layer
derives ownership from the verified session email and permitted license, not
from a project, uploaded file, URL, or form field.

## Database

`db/sonara_project_storage.sql` provisions the current document per account,
append-only saved versions, and a revision-checked save RPC. It has been
applied to the Diplomado Supabase project. Public and `authenticated` roles
have no table or function privileges; RLS is enabled without public policies.
Only the existing server-side service client is permitted. Do not expose its
key in browser code. This design uses SONARA's current custom account system;
it does not claim to use Supabase Auth user JWT policies.

The entire existing project document is retained, including recintos,
requerimientos, soluciones, curves, and costs. Saving a stale revision fails
instead of overwriting changes from another session. A failed read stops the
flow instead of returning an empty document. A failed save offers a JSON
download of pending changes and cannot display a successful save message.

## Before deploying on Render

1. Keep the old instance running while obtaining its private project files.
   Projects are currently on ephemeral storage and are not in Git.
2. Back up the entire `data/projects` directory and any old `data/projects.json`
   separately. A shared legacy file must have its owner explicitly verified;
   it is never automatically copied to whichever user signs in.
3. Make the new migration script and `project_store.py` available on the old
   server, without redeploying it. The script requires the existing
   `academy_access.py`, server dependencies, and server environment variables.
4. Run `python scripts/migrate_project_files.py` for inventory. Only account
   emails are fetched; credentials are not exported. Unknown/ambiguous owners
   are reported for manual resolution.
5. During the cutover, stop edits in the old instance and run
   `python scripts/migrate_project_files.py --apply`. It verifies round trips
   and retains all local originals. Existing different cloud documents are
   reported as conflicts and never overwritten. Resolve every conflict or
   missing owner, including changes made after an earlier import, before
   deploying. Do not treat a partial import as a completed migration.
6. Confirm Render has `SONARA_ACADEMY_SUPABASE_URL` and
   `SONARA_ACADEMY_SUPABASE_SERVICE_ROLE_KEY` (or the supported secret-key
   alternative) set privately. `SONARA_PROJECT_STORAGE` must be `supabase`.
7. Deploy the code, then sign in from a new session, verify projects and saved
   solutions, rename a linked room, and save/reload a change. Check another
   account sees only its own projects.

Private per-account local files remaining on a server are imported once on
first access if no cloud document exists. They never replace an existing cloud
document, and an import error stops the flow without deleting the original.
Verified legacy local accounts are registered in Supabase after password
verification before their project data is written.

## Recovery

Configuración → Datos exports the current cloud document and up to 50 recent
version entries for the signed-in account. Each listed version can be
downloaded. Importing a backup adds missing projects; conflicting current
projects are rejected without writes. The server keeps saved revisions, but
separate database backups/exports remain appropriate for disaster recovery.

## Validation

`python -m unittest discover -s tests -q` covers custom requirements, rename
links and IDs, cloud round trips, account isolation, CAS conflicts, outage
handling, pending changes, and idempotent file migration. Database verification
also checks real service-role writes, revision conflicts, version creation,
RLS, and revoked public privileges in rollback-only test transactions.
