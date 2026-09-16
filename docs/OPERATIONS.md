# Operations

An Operation is one logical user-requested process: `document_analysis`, `document_question`, `reply_draft`, or `reanalysis`. It is not the local Document and it has its own opaque `operation_id`.

## Lifecycle

`accepted -> processing -> succeeded | partial | failed`; `cancelled` and `expired` are allowed when a justified policy/process supports them. An operation records request correlation, relevant client document correlation, type, timestamps, status, safe failure category, retry metadata, and prompt/model/config/schema references. Results can be delivered only once product validation succeeds.

An **attempt** is a provider-facing execution within an operation. One logical operation can have an initial attempt, transient retry, or later fallback attempt. Attempts independently record ordinal, timing, outcome, safe error category, configuration references, and usage/cost. The client sees one operation, not duplicated analyses or charges.

Phase 1 persists these lifecycle values and their timestamps without exposing an operation API or executing work. The domain transition model permits only `accepted -> processing/cancelled/expired` and `processing -> succeeded/partial/failed/cancelled/expired`. An attempt table has a unique positive ordinal per operation; it does not imply a provider was called.

Phase 2.1 adds `OperationResult` as a temporary, operation-linked delivery record for a validated `AnalysisResult`. It has its own opaque ID, explicit schema version, created/expiry timestamps, optional deletion timestamp, and one-result-per-operation invariant. It is not a Document, Flutter’s durable analysis history, uploaded content, or FollowUpContext. Expired/deleted results are not returned; a cleanup worker is intentionally deferred.

Phase 2.2 submission creates an accepted `document_analysis` operation only after request validation and temporary storage succeed. It records a one-to-one `temporary_inputs` metadata row and returns `202`; no worker has started and no analysis result is fabricated. Phase 2.3 will add the PostgreSQL-backed worker to claim accepted operations, load input through `TemporaryDocumentStore`, execute the workflow, persist attempts, and eventually produce `OperationResult`. Phase 2.4 will add provider execution, structured output, prompts, and usage capture.

## Phase 2.3 worker

The worker claims accepted document-analysis operations with PostgreSQL row locking, records bounded attempts and a worker lease, and executes outside the transaction. Retryable technical failures return to `accepted` after a configured delay; non-retryable or exhausted failures become `failed`. Missing or expired storage is `missing_temporary_input`, never a document-quality result. No provider, result, or usage event is fabricated.

## Quality versus infrastructure outcomes

Input/document quality is a valid product result: `partial` or `unavailable` with quality reasons such as unreadable text or missing pages. Infrastructure problems are typed failures: validation/unsupported input, rate limit, quota exhaustion, provider timeout/unavailability/failure, structured output invalid, or unexpected internal error. A retryable technical failure must never be represented as a statement about the document’s quality.

## Async decision

**ADR D-001 chooses asynchronous operation resources for document analysis.** Mobile interruptions, potentially multi-page PDFs, provider latency, retries, idempotency, and future fallback make `POST -> 202 operation_id -> GET status/result` the safer baseline. Small future operations may gain a compatible bounded synchronous completion optimization, but that must not change the operation contract or make clients depend on long-held connections.

## Temporary upload lifecycle

`receive -> validate -> isolated temporary store/process -> provider processing -> result validation -> delete`. Files are generated with safe server names, isolated from executable/public paths, access-limited, and never become cloud documents. Cleanup runs on success, handled failure, expiry, and recovery of orphaned work. Retention is explicit, configurable, bounded, testable, and observable through counts/ages/categories—not content. The exact duration is an open policy question and is not selected here.

## Follow-up context

A later `follow_up_context_id` may reference a minimal cache of validated structured analysis, concise follow-up summary, selected evidence snippets, version, created/expiry timestamps, and deletion state. It excludes original PDFs/images, is not permanent Document storage, has configurable bounded retention, expires automatically, can be explicitly deleted, and must be excluded from ordinary logs/analytics.

Temporary input, OperationResult, and FollowUpContext are three separate lifecycles: original pending-analysis copies, validated result delivery, and later minimized assistant context respectively.
