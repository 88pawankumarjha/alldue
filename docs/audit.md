# Audit Log

## 2026-06-21
- Added Firestore-backed video collections for `videos` and `dev_videos`.
- Added dev-only publish flow from `/dev/` to prod.
- Added repo requirements/audit tracking so future prompts are preserved.
- Enforced dev-first workflow rule.
- Removed dev search debug logs.
- Increased header search icon size.
- Increased footer icon size and reduced footer label size.
- Kept these UI changes limited to `/dev/` until explicit prod approval.
- Wired the `/dev/` footer profile button to the Google sign-in flow.
- Moved dev/prod navigation targets to use route-specific home paths instead of shared `/` links.
