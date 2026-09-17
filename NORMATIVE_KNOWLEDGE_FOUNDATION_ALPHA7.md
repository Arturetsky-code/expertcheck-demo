# ExpertCheck 20.0 Alpha 7 — Normative Knowledge Foundation

## Purpose

Alpha 7 turns the normative layer into a first-class product asset instead of a flat list of citations.

The architecture explicitly separates:

1. **Normative document catalogue** — source, status, edition and official-source trust.
2. **Atomic requirements** — clause-level executable contracts.
3. **Project routing** — which requirements are relevant to the current project and sections.
4. **Project evidence** — addressable proof from the uploaded project.
5. **Expert history corpus** — real remarks, responses and recurrence used for prioritisation and analog search only.

## Why

A large corpus of regulations is useful, but document count is not the same as automated coverage.

ExpertCheck therefore reports separately:
- how many normative documents are known;
- how many status records are curated;
- how many atomic requirements exist;
- how many clauses are verified;
- how many contracts are ready for categorical automation;
- how much expert-history evidence is available.

## Fail-closed policy

An automatic normative verdict requires:
- a curated active source;
- a verified clause address;
- a project applicability route;
- addressable project evidence;
- a supported verification contract;
- categorical conclusion permission where required.

A repeated expert remark never becomes an automatic norm or verdict by repetition alone.

## Expert-history corpus

The existing project evidence library under `knowledge/evidence/projects` contains real expert remark/response records.

Alpha 7 indexes this corpus as:
- historical projects;
- remarks;
- responses;
- resolved remarks;
- repeat/clarification cycles;
- normative bases;
- recurring section/violation patterns.

Usage policy: `PRIORITIZATION_AND_ANALOGS_ONLY`.

The corpus may raise review priority or suggest analogs. It cannot upgrade a clause to VERIFIED_ONLY and cannot create VERIFIED_OK or PROJECT_FINDING without an independent current-project proof.

## User workspace

Developer mode now exposes **НТД и практика** with:
- normative catalogue metrics;
- verified-clause backlog;
- project-specific normative routing;
- expert-history statistics;
- recurring expert-practice patterns;
- explicit trust and automation status for every routed requirement.

## Generalisation

The foundation is project-neutral. The DSK/Test 77/78 controls remain regression fixtures only. New projects are routed from their own document inventory and applicability contracts.
