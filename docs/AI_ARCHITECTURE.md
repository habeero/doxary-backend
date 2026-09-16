# AI architecture

AI is an infrastructure capability behind application-facing responsibilities equivalent to `AIProvider`, `ModelRouter`, `PromptRegistry`, and `StructuredOutputValidator`. These names describe responsibilities, not a premature fixed Python inheritance hierarchy.

- **AIProvider:** converts a normalized request to a provider call and normalizes provider result/error/usage into infrastructure-neutral data.
- **ModelRouter:** selects an enabled configuration by capability/purpose, quality/cost policy, and fallback rules. Purposes include `document_analysis`, `document_question`, `reply_draft`, and `reanalysis`.
- **PromptRegistry:** resolves immutable versioned prompt definitions.
- **StructuredOutputValidator:** validates provider output against the product schema, semantic rules, compatibility, uncertainty rules, and evidence constraints before it becomes Doxary data.

Provider-specific SDK types, concrete model names, request/response formats, and credentials remain infrastructure/configuration. Domain/application code does not import them. The initial anticipated provider does not constitute an implementation or commitment in this phase.

## Prompt strategy

Prompts will be registered and versioned with identifier, version, purpose, expected inputs, output schema version, safety/behavior rules, and where appropriate synthetic/redacted evaluation fixtures. Prompt/model/config references are recorded on operations and usage events, allowing regressions in quality or cost to be correlated without storing source content. Prompts are not scattered string literals.

## Trust boundary and no-fabrication policy

Provider output is untrusted external input. Validate syntax/schema, types/enums/ranges, semantic relations, evidence references, and compatibility before return. Missing or unknown facts remain omitted/null/uncertain as contractually defined. Bounded retries are allowed for transient transport or invalid-output cases; fallback follows explicit routing policy. The system must return `partial` or `unavailable`, never invent a sender, deadline, obligation, evidence, or reply fact. Document text is hostile input: isolate it as quoted source material and do not permit it to override system safety instructions.
