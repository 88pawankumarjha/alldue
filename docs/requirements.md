# Requirements

## Current Rules
- All UI and behavior changes must be applied to `/dev/` first.
- `/` production UI must remain unchanged until the user explicitly asks to promote a change.
- Each new prompt that changes scope should be reflected here before promotion.

## Product Goals
- Archive.org remains the media source.
- Firestore stores metadata only.
- Admin approval for dev-to-prod publishing happens inside the site.
- The site should feel mobile-first on both desktop and mobile.

## UI Rules
- Dev shell may diverge from prod shell.
- Dev and prod must not share UI navigation targets; logo and footer Home must stay within their own route space.
- Footer navigation should be present.
- Top header should be compact.
- Search/profile controls may be inert until explicitly enabled.
- Dev search icon must be larger and functional.
- Footer icons should be larger with smaller labels for a tighter mobile-style layout.
- On `/dev/`, the footer profile button should open Google sign-in when auth is enabled.
- Anonymous likes should be one-per-browser/IP fingerprint.
- Comments should land in a pending queue and only be visible after admin approval on `/dev/`.
- `/dev/` should show visible action buttons for Like, Subscribe, and Comment with counts.
- Prod should not show dev action controls or comment blocks.
- Action and comment UI should visually resemble a compact YouTube mobile layout.
- Like and Subscribe should update counts without a full page reload.
- Action buttons should be flatter, tighter, and more icon-led like YouTube mobile.
- Footer should only show Home for now; remove the profile footer control.
- Put search in the footer instead of the top-right header.

## Tracking Rules
- Every requested change should also be appended to `docs/audit.md`.
- Do not promote dev changes to prod without explicit user approval.
- Dev and prod must use separate templates.
- Changes to dev UI must never alter prod UI by shared template edits.
- Page title should be `Nikhil Funtime`, with the current video name appended on a single-video view.
- Remove the visible `Open Archive` link from the watch page.
- The fullscreen button should toggle both enter and exit fullscreen.
- The quality selector overlay should fade out after 3 seconds and reappear on video click.
