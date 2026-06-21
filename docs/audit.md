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
- Added anonymous fingerprint-based like dedupe and comment moderation queue.
- Added `/dev/` comment approval actions for admin review.
- Made Like, Subscribe, and Comment buttons visible in the `/dev/` UI with counts.
- Hid dev action/comment blocks from prod and restyled them closer to a compact mobile video app layout.
- Switched Like/Subscribe to AJAX so counts update in place without reloading the full page.
- Flattened dev action buttons and tightened comment cards toward a YouTube mobile look.
- Removed the footer profile control so only Home remains in the footer.
- Moved the search control from the header into the footer.
- Split rendering into separate dev and prod templates.
