-- Server-only storage for SONARA's existing authenticated-account model.
-- The Streamlit server scopes each request to its authenticated session email.
-- No browser/public-role access or SECURITY DEFINER functions are used.
create table public.sonara_project_documents (
  owner_email text primary key references public.sonara_accounts(email),
  payload jsonb not null default '{}'::jsonb check (jsonb_typeof(payload) = 'object'),
  revision bigint not null check (revision >= 1),
  updated_at timestamptz not null default now(),
  check (owner_email = lower(btrim(owner_email)))
);
create table public.sonara_project_versions (
  owner_email text not null references public.sonara_project_documents(owner_email),
  revision bigint not null,
  payload jsonb not null check (jsonb_typeof(payload) = 'object'),
  created_at timestamptz not null default now(),
  primary key (owner_email, revision)
);
alter table public.sonara_project_documents enable row level security;
alter table public.sonara_project_versions enable row level security;
revoke all on public.sonara_project_documents, public.sonara_project_versions from public, anon, authenticated;
grant select, insert, update on public.sonara_project_documents to service_role;
grant select, insert on public.sonara_project_versions to service_role;

create function public.sonara_save_project_document(
  p_owner_email text, p_payload jsonb, p_expected_revision bigint
) returns bigint language plpgsql security invoker set search_path = '' as $$
declare
  v_revision bigint;
  v_payload jsonb;
  v_email text := lower(btrim(p_owner_email));
begin
  if v_email is null or v_email = '' or p_payload is null or jsonb_typeof(p_payload) <> 'object'
     or p_expected_revision is null or p_expected_revision < 0 then
    raise exception 'Invalid SONARA project document';
  end if;
  -- Serialize first inserts as well as updates for this account.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(v_email, 0));
  select d.revision, d.payload into v_revision, v_payload
    from public.sonara_project_documents d where d.owner_email = v_email for update;
  if coalesce(v_revision, 0) <> p_expected_revision then
    raise exception using errcode = '40001', message = 'SONARA_REVISION_CONFLICT';
  end if;
  if v_revision is not null and v_payload = p_payload then
    return v_revision;
  end if;
  v_revision := coalesce(v_revision, 0) + 1;
  insert into public.sonara_project_documents(owner_email, payload, revision)
    values (v_email, p_payload, v_revision)
    on conflict (owner_email) do update
      set payload = excluded.payload, revision = excluded.revision, updated_at = now();
  insert into public.sonara_project_versions(owner_email, revision, payload)
    values (v_email, v_revision, p_payload);
  return v_revision;
end;
$$;
revoke all on function public.sonara_save_project_document(text, jsonb, bigint) from public, anon, authenticated;
grant execute on function public.sonara_save_project_document(text, jsonb, bigint) to service_role;
