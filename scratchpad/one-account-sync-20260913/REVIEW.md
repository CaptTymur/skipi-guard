# One-account sync route review

Status: DRAFT; native final functional path scope reconciled: exactly 13 paths, no missing or extra paths. Human merge required. Product runtime correctness remains pending.

The complete profile, sea-service and document sync implementation spans account/vault lifecycle and destructive writers. Its combined diff currently falls through to plugin-host and fails scope. This adds one non-release task, `one-account-sync-192`, with the same 13 literal paths in the exact set, allowed patterns, routing set and required set. All 13 are mandatory. No wildcard, protected-path, release-path, release-task or override change. Existing routes retain order.

Base: live SSH `a6904f60ec2b46535dba2ce54faecc43083f84a7`, including PR60's canonical iOS plist version-bump change. Initial ops proposal and supervisor source audit used a621041; their reviewed delta was reapplied to live main. The necessary thirteenth path, ai.rs, was identified by native implementation and approved by the manager for stale-write protection only.

## Exact path justification

| Path | Purpose |
|---|---|
| `dist/index.html` | Explicit opt-in, account binding, sync status, retry/conflict UI and scheduling. |
| `src-tauri/src/commands/account_sync.rs` | Shared desktop/mobile engine, durable queue, CAS inventory and recovery. |
| `src-tauri/src/commands/ai.rs` | Guard existing document metadata writes in update_field_statuses and recognize_document with displayed revision and vault session; no AI provider, model or prompt change. |
| `src-tauri/src/commands/app_login.rs` | Invalidate and pin session across asynchronous login/logout. |
| `src-tauri/src/commands/account_delete.rs` | Prevent a delayed deletion response from changing a different open vault. |
| `src-tauri/src/commands/vault.rs` | Pin vault identity and cancel pending work on open/close. |
| `src-tauri/src/commands/profile.rs` | Preserve replaced profile photo before destruction. |
| `src-tauri/src/commands/documents.rs` | Preserve deleted or replaced document bytes before destruction. |
| `src-tauri/src/commands/work_history.rs` | Preserve evidence and separate storage identity from editable IMO/date. |
| `src-tauri/src/db.rs` | Add persistent per-account sync ledger without destructive migration. |
| `src-tauri/src/lib.rs` | Register shared state and sync commands. |
| `tests/account_profile_sync_harness.mjs` | Update existing manual-profile privacy regression for explicit opt-in. |
| `tests/one_account_sync_harness.mjs` | Add sync UI/command behavior regression. |

On 2026-09-13 the native executor froze the final functional scope at these 13 paths. An independent read of its worktree found the same 12 tracked changed files plus the new `tests/one_account_sync_harness.mjs`; no functional path was missing or extra. Native scratch artifacts are excluded from this product source inventory and are not allowed by this route. This is a scope reconciliation only: implementation bytes and product tests are still being completed.

The previous ten mobile-189-native harness commands remain in full, followed by account_profile_sync and one_account_sync. The existing profile harness is genuinely changed to reflect explicit opt-in; it is not changed merely to satisfy this route.

## Validation

New regression was run before the config change: exact full diff auto-routing was RED as plugin-host, with concrete scope violations. After the change the seven tests pass: real CLI auto and explicit routing, each missing required file, eight unrelated/protected/release extras, empty explicit task, all twelve harness failures propagated with subprocess stubs, seven policy mutations detected, and the whole prior parsed config SHA256 preserved after removing only the new task. Fixture Git/files stay inside this worktree scratch prefix; harness commands are stubbed and no product behavior is asserted.

Prior config canonical JSON hash: `90494abb14bd68b69a829892111d7890a7bf068fd78ab457636e9f0f840bd8c7`. Candidate config byte SHA256: `dd6d6ef009572c0765c19909049aef256fea2cba4d3597364415ad2dfca89ba7`.

`python3 -m unittest discover -s tests`: **400 tests PASS**, 63.852 seconds, matching the repository CI command. Raw RED, initial full-suite failures, corrected route GREEN and final full-suite output are preserved as gzip logs alongside this review.

Seven older route test files have narrowly named exclusions for this new task in historical global count/key/hash assertions. Their previous routing, protection, release, harness and negative checks remain. The prior ai.rs route continues to prohibit document edits; only this new exact thirteen-file task has the explicitly justified documents.rs allowance.

This PR does not install Guard or update any native CI pin. Guard human merge, installed hook enforcement and the later exact native CI pin update remain separate. Native product tests remain with the native executor; the completed path reconciliation does not establish runtime sync correctness.
