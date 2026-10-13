# Phase 3: Topics and materials (F3, F4)
Read `.github/copilot-instructions.md` and `docs/SCOPE.md`. Build ONLY F3 and F4.

Topics: CRUD under `/courses/{id}/topics`, max 10 per course, fields name, module_label, description (required, one sentence).
On create/update/delete, enqueue a job that re-tags the course's chunks with their nearest topic (cosine over embeddings; threshold from Settings).
Materials: POST multipart upload (PDF, PPTX, DOCX, IPYNB, MD, TXT; max `MAX_UPLOAD_MB`, 50 per course). Validate by extension AND content sniff;
sanitise filenames; store through `FileStorage`; create the Material row with status `processing`, enqueue ingestion via `Jobs`, return immediately.
Ingestion: extract sections, chunk, embed, tag with topic, add to `VectorStore` with metadata course_id, material_id, section, topic_key. Status becomes `indexed` or `failed` with a short human-readable error (e.g. "This PDF has no selectable text (scanned?)").
All vector queries MUST filter by course_id. DELETE material removes file, vectors and row. GET list shows status and chunk count.
Frontend: Topics setup page and Materials page with status polling every 3 seconds while anything is processing, and clear error messages.
Tests: chunking, file validation, course isolation of vectors (course A query never returns course B chunks), delete removes vectors, topic limit.
Do NOT: add OCR, auto-suggested topics, previews other than PDF, folders, versioning.
Done when: tests + build pass. Human check: upload 3 real files (a PDF, a PPTX, an IPYNB) and confirm they reach `indexed`; upload a scanned PDF and confirm a clear failure message.
