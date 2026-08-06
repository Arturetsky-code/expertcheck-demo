# ExpertCheck 5.0 Alpha 1 — Cognitive Document Intelligence

## Processing order

1. Classify every PDF page as service content, official object register, object/TEP table, drawing, or narrative text.
2. Extract tables as matrices when PyMuPDF can identify their rows and cells.
3. Create project objects only from official registers and object/property tables.
4. Bind every TEP to the object in the same table row (`ROW_LOCKED`).
5. Keep narrative mentions as evidence only; they cannot independently create a project object.
6. Compile checklist questions into numeric, presence, parameter-evidence, or semantic-review rules.
7. Optionally send only ambiguous object/checklist fragments to OpenRouter or Groq for structured JSON review.
8. Never let an external AI modify the Trusted Object Registry without user confirmation.

## New evidence fields

- `table_row`
- `table_column`
- `table_header`
- `table_evidence`
- `binding_status=ROW_LOCKED`
- `cognitive_extraction=true`

## External AI

The setting `Использовать внешний AI для неоднозначных объектов и пунктов чек-листов` is opt-in. Full PDFs are not sent. AI decisions are recommendations and remain outside deterministic Core results until the user confirms them.
