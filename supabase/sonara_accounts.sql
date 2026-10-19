-- Private, server-side account store for SONARA.
-- Apply this to the Diplomado Supabase project. Public roles receive no access;
-- SONARA reaches it only through its deployment secret key.
create table if not exists public.sonara_accounts (
  email text primary key check (email = lower(btrim(email))),
  password_hash text not null,
  salt text not null,
  nombre text not null default '',
  empresa text not null default '',
  cargo text not null default '',
  first_login timestamptz not null default now(),
  last_login timestamptz not null default now(),
  license_type text not null default 'trial'
    check (license_type in ('trial', 'academy', 'premium', 'developer')),
  estado text not null default 'active'
    check (estado in ('active', 'inactive', 'expired')),
  trial_start timestamptz,
  trial_end timestamptz,
  updated_at timestamptz not null default now()
);

alter table public.sonara_accounts enable row level security;
revoke all on table public.sonara_accounts from anon, authenticated;
grant select, insert, update, delete on table public.sonara_accounts to service_role;

create policy "sonara_accounts_no_public_access"
on public.sonara_accounts
for all
to anon, authenticated
using (false)
with check (false);

comment on table public.sonara_accounts is
  'Private SONARA credentials and license cache; server-side service key only.';
