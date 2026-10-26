# SETU frontend patch notes

Changes in this patch:
1. Replaced the manually pasted bearer-token workflow with Supabase Auth email/password sign-in.
2. Hide the dashboard until a Supabase session is established; protected API calls start only after login.
3. Add sign-out and clear the displayed protected data when the session ends.
4. Add working A+ / A− controls that scale the full interface from 85% to 125% and persist the setting.
5. Add a persistent dark/light theme toggle.
6. Update `.env.example` and README with Supabase configuration and security notes.

Security boundary: the frontend is not the authorization authority. FastAPI must continue validating the bearer token and the user's linked staff profile/role. Never use a Supabase service-role key in frontend configuration.

Build status: not verified in this environment because `npm install` did not finish before timeout. Run `npm install` and `npm run build` locally after extracting.
