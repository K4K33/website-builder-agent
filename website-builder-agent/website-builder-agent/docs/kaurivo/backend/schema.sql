-- KAURIVO ONLY: intended for a distinct Supabase project, NOT OAVIR.
-- No data from prospective or actual customers belongs in this repository.
-- Apply only after selecting the Kaurivo Supabase organization and reviewing privacy.
-- Requires PostgreSQL 15+, pgcrypto provided by Supabase.

create extension if not exists pgcrypto with schema extensions;

create table if not exists public.kaurivo_feedback_invitations (
  id uuid primary key default gen_random_uuid(),
  token_sha256 text not null unique
    check (token_sha256 ~ '^[0-9a-f]{64}$'),
  internal_project_ref text not null,
  verified_client_email text not null,
  verified_company text not null,
  sale_confirmed_at timestamptz not null,
  expires_at timestamptz not null,
  used_at timestamptz,
  created_at timestamptz not null default now(),
  constraint invite_valid_dates check (expires_at > sale_confirmed_at),
  constraint email_length check (length(verified_client_email) between 3 and 254),
  constraint project_length check (length(internal_project_ref) between 4 and 100)
);

create table if not exists public.kaurivo_feedback_submissions (
  id uuid primary key default gen_random_uuid(),
  invitation_id uuid not null unique references public.kaurivo_feedback_invitations(id),
  rating smallint not null check (rating between 1 and 5),
  comment_text text not null check (length(btrim(comment_text)) between 3 and 2000),
  submitted_email text not null check (length(submitted_email) between 3 and 254),
  submitted_company text not null check (length(submitted_company) between 1 and 120),
  submitted_at timestamptz not null default now(),
  topic text not null,
  priority text not null check (priority in ('urgent_review', 'normal_review', 'clarify')),
  source_verified boolean not null default false,
  human_reviewed_at timestamptz,
  publicly_approved_at timestamptz,
  public_approval_record text,
  constraint public_approval_needs_record check
    (publicly_approved_at is null or (public_approval_record is not null and length(public_approval_record) > 5))
);

-- The tables are not readable/writable by public visitors or signed-in users.
alter table public.kaurivo_feedback_invitations enable row level security;
alter table public.kaurivo_feedback_submissions enable row level security;
revoke all on public.kaurivo_feedback_invitations from public, anon, authenticated;
revoke all on public.kaurivo_feedback_submissions from public, anon, authenticated;
grant select, insert, update on public.kaurivo_feedback_invitations to service_role;
grant select, insert, update on public.kaurivo_feedback_submissions to service_role;

-- One-time invite submission is atomic (FOR UPDATE + used_at in one transaction).
-- The service-role-only security invoker function is callable solely by the
-- privileged Edge Function. No RLS-bypassing SECURITY DEFINER code is exposed.
create or replace function public.kaurivo_submit_invited_feedback_v2(
  p_token_sha256 text, p_rating int, p_comment text,
  p_email text, p_company text
) returns boolean
language plpgsql
security invoker
set search_path = pg_catalog, public
as $function$
declare
  v_invitation uuid;
  v_topic text;
  v_priority text;
  v_lower text;
begin
  if p_token_sha256 is null or p_token_sha256 !~ '^[0-9a-f]{64}$'
    or p_rating is null or p_rating not between 1 and 5
    or p_comment is null or length(btrim(p_comment)) not between 3 and 2000
    or p_email is null or length(btrim(p_email)) not between 3 and 254
    or p_email !~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'
    or p_company is null or length(btrim(p_company)) not between 1 and 120
  then
    return false;
  end if;

  select id into v_invitation
  from public.kaurivo_feedback_invitations
  where token_sha256 = p_token_sha256
    and used_at is null and expires_at > now()
    and sale_confirmed_at <= now()
    and lower(btrim(verified_client_email)) = lower(btrim(p_email))
  for update;

  if v_invitation is null then
    return false;
  end if;

  v_lower := lower(p_comment);
  v_priority := case
    when v_lower ~ '(ei toimi|cannot submit|broken|tietovuoto|tietoturva|security|payment failed)'
      then 'urgent_review'
    when length(btrim(p_comment)) < 20
      then 'clarify'
    else 'normal_review'
  end;
  v_topic := case
    when v_lower ~ '(mobiili|mobile|iphone|valikko|menu)' then 'mobile_usability'
    when v_lower ~ '(hidas|nopeus|slow|speed|lataa)' then 'performance'
    when v_lower ~ '(lomake|form|bug|virhe|error|broken)' then 'functionality'
    when v_lower ~ '(wordpress|muokata|edit|cms)' then 'editing'
    when v_lower ~ '(viesti|vastaus|yhteydenpito|reply|communication)' then 'communication'
    when v_lower ~ '(kuva|logo|vär|colour|content)' then 'brand_content'
    else 'general_experience'
  end;

  insert into public.kaurivo_feedback_submissions (
    invitation_id, rating, comment_text, submitted_email, submitted_company, topic, priority
  ) values (v_invitation, p_rating, btrim(p_comment), lower(btrim(p_email)), btrim(p_company), v_topic, v_priority);
  update public.kaurivo_feedback_invitations
    set used_at = now()
    where id = v_invitation and used_at is null;
  return true;
end;
$function$;

revoke all on function public.kaurivo_submit_invited_feedback_v2(text, int, text, text, text)
  from public, anon, authenticated;
grant execute on function public.kaurivo_submit_invited_feedback_v2(text, int, text, text, text)
  to service_role;

-- Do not add anon SELECT/INSERT policies or expose raw feedback via a view.
-- Keep admin review in the authenticated Supabase dashboard / privileged
-- ChatGPT connector, not in the public GitHub Pages website.
