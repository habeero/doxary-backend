# Product context

Doxary helps people in Germany understand formal German documents and identify practical next steps. Its primary flow is: the Flutter app imports an image/PDF locally, a user requests analysis, the backend processes the selected upload temporarily, and the client stores the validated structured result locally. Initial explanation choices are Arabic and German with a simple style; language and style are separate extensible preferences.

The product is document-first. Conversation is secondary and scoped to a document: explain a point, answer a document question, or draft a German reply. It is not a generic chatbot, legal adviser, or cloud document-management system.

## Local-first ownership

The Flutter app remains the durable MVP authority for Organizations, Cases, Documents, document files, analysis history, tasks, deadlines, appointments, user corrections, and preferences. A client upload does not create a server Document. The backend may retain only its operational responsibilities: processing operations/attempts, idempotency records, privacy-safe usage/cost events, and later minimal follow-up context.

One logical local Document can be one image, multiple ordered images/pages, or one PDF. On-device OCR and a separate OCR pipeline are not MVP prerequisites. User corrections are authoritative product state and must never be silently overwritten by automated suggestions.

## Explicit non-goals

Phases 1 through 2.5 implement the backend foundation, temporary upload/worker/provider path, provider-neutral validated analysis contract, temporary result persistence, and public operation delivery. Flutter remains the durable product owner and Flutter-to-staging integration is still pending. The backend is not a generic Habeero platform, multi-tenant application registry, microservice suite, account system, sync service, permanent cloud-file store, billing system, or unrestricted provider integration.
