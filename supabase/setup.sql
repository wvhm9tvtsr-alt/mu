-- Run once in the Supabase project's SQL Editor. Safe to run again.
begin;
create table if not exists public.mu_sync_documents (
  user_id uuid primary key references auth.users(id) on delete cascade,
  revision bigint not null check (revision > 0),
  payload jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.mu_sync_documents enable row level security;
revoke all on public.mu_sync_documents from public, anon, authenticated;
grant select on public.mu_sync_documents to authenticated;
drop policy if exists mu_read_own_document on public.mu_sync_documents;
create policy mu_read_own_document on public.mu_sync_documents for select to authenticated using ((select auth.uid()) = user_id);
-- All writes go through a compare-and-swap operation, never a blind overwrite.
create or replace function public.mu_save_document(p_expected_revision bigint, p_payload jsonb)
returns table(revision bigint, updated_at timestamptz)
language plpgsql security definer set search_path = '' as $$
declare
  v_user uuid := auth.uid();
  v_revision bigint;
  v_updated timestamptz;
  v_count integer;
begin
  if v_user is null then raise exception 'Authentication required' using errcode = '42501'; end if;
  if p_expected_revision is null or p_expected_revision < 0 or p_payload is null
     or jsonb_typeof(p_payload) <> 'object' or p_payload->>'version' is distinct from '1'
     or jsonb_typeof(p_payload->'data') is distinct from 'object'
     or octet_length(convert_to(p_payload::text, 'UTF8')) > 8388608 then
    raise exception 'Invalid sync payload' using errcode = '22023';
  end if;
  select d.revision into v_revision from public.mu_sync_documents d where d.user_id = v_user for update;
  if not found then
    if p_expected_revision <> 0 then raise exception 'mu_sync_conflict' using errcode = '40001'; end if;
    insert into public.mu_sync_documents(user_id, revision, payload) values (v_user, 1, p_payload)
      on conflict (user_id) do nothing;
    get diagnostics v_count = row_count;
    if v_count <> 1 then raise exception 'mu_sync_conflict' using errcode = '40001'; end if;
  else
    if v_revision <> p_expected_revision then raise exception 'mu_sync_conflict' using errcode = '40001'; end if;
    update public.mu_sync_documents d set revision = d.revision + 1, payload = p_payload, updated_at = now()
      where d.user_id = v_user;
  end if;
  select d.revision, d.updated_at into v_revision, v_updated from public.mu_sync_documents d where d.user_id = v_user;
  return query select v_revision, v_updated;
end;
$$;
revoke all on function public.mu_save_document(bigint, jsonb) from public, anon;
grant execute on function public.mu_save_document(bigint, jsonb) to authenticated;
commit;
