# Structured AI output schemas

The stable common analysis envelope is the product boundary. It is versioned and typed; it is neither arbitrary provider JSON nor a giant mandatory authority-specific record. Category-specific typed extensions may be introduced under later schema versions when a real category needs one.

## DocumentAnalysis envelope (directional v1)

Required envelope concepts: `schema_version`, `client_document_id`, `analysis_status`, `detected_language`, `action_required`, `urgency`, `uncertainties`, `quality_reasons`, `extracted_facts`, `explanation`, and `source_references`. Optional, typed facts include sender/organization suggestion, document type/date, practical states, deadlines, appointments, amounts, required documents, and suggested tasks.

Directional typed values keep their own optionality: a deadline has label, date/date range, optional time/timezone, consequence, confidence, and evidence; an appointment has label, date/start and optional end/location/preparation/evidence; an amount has value, ISO currency, pay/receive/unknown direction, optional due date/purpose/evidence; a required document has description, optional due date/submission method/evidence; and a suggested task has title, optional due date/instructions/linked-deadline evidence. `practical_states` is a non-exclusive typed set (for example informational, action required, payment, appointment, documents required), not a single forced classification.

`analysis_status` is `complete`, `partial`, or `unavailable`. Input-quality reasons are machine-readable: `blurry_image`, `page_cut_off`, `unreadable_text`, `missing_pages`, `unsupported_file`, `corrupt_file`, and `insufficient_content`. They are distinct from infrastructure/API failures.

Facts and explanation are separate. A deadline fact such as `2026-09-30` does not change when its meaning is explained in Arabic versus simple German. Explanation carries separate `language` and `style` values; Arabic is an initial option, not domain logic. Optional facts are omitted or explicit unknown values, never fabricated mandatory filler.

Each material extracted fact can contain a typed evidence reference, for example input file/page, bounded relevant location, and optionally a selected source snippet label. Evidence has provenance `analysis`, `user`, or `system`. Full OCR text persistence is not a requirement. User corrections remain authoritative and retain their provenance.

## Assistant results

Question and reply-draft schemas are also versioned and document-scoped. A question answer includes an answer language, uncertainties, and evidence references. A German reply draft includes purpose, assumptions, missing information, and optional explanatory translation. Both must clearly surface absent context instead of inventing information.
