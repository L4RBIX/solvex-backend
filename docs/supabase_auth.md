# Supabase Auth setup and rollback

SolveX treats Supabase Auth and Codeforces ownership as two separate layers:

`Supabase sub -> auth_identities -> users.user_id -> optional handle_owners row`

All private authorization uses the internal `user_id`. Email, OAuth provider
metadata, display names, request identity fields, and public Codeforces handles
never select the authorized user.

## Supabase Dashboard

1. In **Authentication > Providers**, keep Email enabled and enable email
   confirmation for production. Configure a production SMTP provider; the
   default sender is intended only for low-volume testing.
2. In **Authentication > URL Configuration**, set Site URL to the production
   frontend origin. Add exact production callbacks and local callbacks:
   - `https://solvex-frontend-omega.vercel.app/auth/callback`
   - `http://localhost:3000/auth/callback`
   Add a Vercel preview wildcard only when preview OAuth is required, for
   example `https://*-<team-or-account-slug>.vercel.app/auth/callback`.
3. In **Authentication > JWT Keys**, use an asymmetric ES256 or RS256 signing
   key. Stage/rotate the key according to Supabase guidance before retiring the
   old key. A legacy HS256 secret is not published through JWKS and will fail
   closed in this backend.
4. Confirm the public JWKS endpoint returns keys:
   `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`.
5. Do not put the service-role/secret key in the frontend. SolveX JWT
   verification needs only public signing keys and does not require a
   service-role key.

## Google OAuth

1. In Google Auth Platform, create a **Web application** OAuth client.
2. Add the production frontend origin and any explicitly supported local
   origin under Authorized JavaScript origins.
3. Add the Supabase callback shown on the Supabase Google provider page under
   Google Authorized redirect URIs. It has the form:
   `https://<project-ref>.supabase.co/auth/v1/callback`.
4. Put the Google client ID and secret only in **Supabase Authentication >
   Providers > Google**, then enable the provider.
5. The frontend sends users back through `/auth/callback`. Every final `next`
   value is restricted to a relative same-origin path to prevent open redirects.

## Email and password reset

- Email sign-up confirmation returns through `/auth/callback`.
- Forgot-password always shows the same confirmation, whether or not the email
  exists.
- A reset link returns through `/auth/callback?next=/auth/reset-password`.
- The update form requires both an authenticated Supabase session and the
  `PASSWORD_RECOVERY` auth event. An ordinary login callback cannot mark a
  session as recovery.
- Review confirmation/recovery email templates when using `redirectTo`; ensure
  they preserve the requested allowlisted redirect rather than hard-coding an
  unrelated site URL.

## Environment names

Railway backend (private configuration):

```text
SUPABASE_URL
SUPABASE_JWT_ISSUER
SUPABASE_JWT_AUDIENCE
SUPABASE_JWKS_URL
```

Vercel frontend (public project configuration):

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

The anon/publishable key is designed for browser use; authorization still
comes from a user's signed access token. Never add a service-role/secret key to
Vercel.

## Release order and rollback

1. Back up the persistent SQLite database and apply migration 022 (or let the
   additive SQLite mirror create the table at startup).
2. Configure Supabase and platform environment values without changing
   `DATABASE_PATH` or the mounted volume.
3. Deploy backend first, verify JWT login and `/api/v1/auth/me`, then deploy the
   frontend.
4. To roll back application code, redeploy the preceding backend and frontend
   commits. Leave `auth_identities` and migration 022 in place: the table is
   additive and harmless to the old code. Do not roll back by deleting users,
   handle ownership, entitlements, or historical events.
5. If auth must be disabled during an incident, roll back both applications as
   a matched pair. Removing JWT variables while the new production backend is
   active intentionally makes startup fail closed.

Existing paid-beta users are not automatically merged by email or handle.
Such matching is not proof of account ownership. Any legacy entitlement or
verified-handle reconciliation requires an explicit, audited support decision.
