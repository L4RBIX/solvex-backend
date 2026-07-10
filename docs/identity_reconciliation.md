# Verified-handle reconciliation

SolveX authorizes private account actions only with the bearer-token identity
`user:<internal_user_id>`. A public Codeforces handle, including historical
`handle:<handle>` product events, never grants account access.

Self-service verification binds a handle only after a live Codeforces profile
check. Existing pre-verification rows are not automatically transferred,
deleted, or rewritten. Once ownership is verified, the handle alias may be
used for read-only aggregation of that owner's historical public telemetry;
it is not an authorization identity.

There is intentionally no automatic ownership transfer or unbind operation.
Support may use the audited `POST /api/v1/admin/handles/bind` reconciliation
endpoint after manually establishing ownership. It will not replace another
account's existing binding. A disputed or transferred Codeforces handle
therefore requires a separate, explicitly reviewed administrative procedure.

Legacy rows can remain stranded when their old public handle cannot be safely
matched to a verified SolveX account. This is preferable to assigning private
history to the first person who requests a public handle. Account deletion
removes that account's claim and ownership rows but does not destructively
rewrite historical public-handle telemetry. In particular, a legacy private-
leaderboard member with no internal `user_id` remains visible for audit but is
scored at zero; otherwise new anonymous analysis of its public handle could
change private standings. The verified account must explicitly rejoin the
leaderboard through an invite after support review.
