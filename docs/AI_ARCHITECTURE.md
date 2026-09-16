# AI architecture

AI is an infrastructure capability behind application-facing responsibilities equivalent to `AIProvider`, `ModelRouter`, `PromptRegistry`, and `StructuredOutputValidator`. These names describe responsibilities, not a premature fixed Python inheritance hierarchy.

- **AIProvider:** converts a normalized request to a provider call and normalizes provider result/error/usage into infrastructure-neutral data.
- **ModelRouter:** selects an enabled configuration by capability/purpose, quality/cost policy, and fallback rules. Purposes include `document_analysis`, `document_question`, `reply_draft`, and `reanalysis`.
- **PromptRegistry:** resolves immutable versioned prompt definitions.
- **StructuredOutputValidator:** validates provider output against the product schema, semantic rules, compatibility, uncertainty rules, and evidence constraints before it becomes Doxary data.

Provider-specific SDK types, concrete model names, request/response formats, and credentials remain infrastructure/configuration. Domain/application code does not import them. The initial anticipated provider does not constitute an implementation or commitment in this phase.

## Phase 2.4 provider adapter

Phase 2.4 provides an opt-in OpenAI Responses API adapter behind the worker executor boundary. It sends a PDF as a temporary provider file or ordered images as one request, requests strict typed structured output, and returns only validated Doxary `AnalysisResult` values. The adapter derives a transport-only schema that omits strict-mode-unsupported domain constraints; the full Doxary contract still revalidates every returned value. Model, timeout, and optional reasoning effort are infrastructure configuration; the SDK has zero internal retries so the worker owns bounded retries.

Provider failures retain only bounded technical diagnostics on the operation attempt (exception class, HTTP status, provider code/type, and request ID where available). The server injects Doxary's local `client_document_id` and fixed schema version after provider output and before domain validation, so server-owned identifiers are not part of the provider schema. Request content, provider messages, raw payloads, and credentials are never retained.

Document-analysis Responses requests explicitly set `store=False`. Usage and latency are captured for every provider response before Doxary mapping; mapping or domain-validation failure still records a failed `UsageEvent` and cost when pricing is known, but never creates an `OperationResult`.

The live Phase 2.4 image smoke verification succeeded through Responses, strict transport output, backend injection, `AnalysisResult v1`, `OperationResult`, `UsageEvent`, and local cleanup. Provider-file cleanup was not applicable because the verified path used an image rather than an uploaded PDF. Cost was unavailable because `gpt-5.6-luna` has no configured pricing snapshot.

The provider transport schema contains model-generated fields only. Doxary injects server-owned `client_document_id` and `schema_version`; `AnalysisResult v1` remains authoritative. Model selection is runtime-configurable and separate from pricing snapshots. An unpriced model still records usage, but estimated cost is null—Doxary never fabricates a price.

## Prompt strategy

Prompts will be registered and versioned with identifier, version, purpose, expected inputs, output schema version, safety/behavior rules, and where appropriate synthetic/redacted evaluation fixtures. Prompt/model/config references are recorded on operations and usage events, allowing regressions in quality or cost to be correlated without storing source content. Prompts are not scattered string literals.

## Trust boundary and no-fabrication policy

Provider output is untrusted external input. Validate syntax/schema, types/enums/ranges, semantic relations, evidence references, and compatibility before return. Missing or unknown facts remain omitted/null/uncertain as contractually defined. Bounded retries are allowed for transient transport or invalid-output cases; fallback follows explicit routing policy. The system must return `partial` or `unavailable`, never invent a sender, deadline, obligation, evidence, or reply fact. Document text is hostile input: isolate it as quoted source material and do not permit it to override system safety instructions.
