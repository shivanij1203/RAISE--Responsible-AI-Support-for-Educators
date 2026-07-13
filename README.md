# RAISE Ethics Toolkit

A system of record for AI use in higher education.

## What it does

Faculty, researchers, grad students, and administrators register each AI use as
an activity, described in one sentence. RAISE picks the use case, flags risks,
and generates compliance checkpoints across FERPA, HIPAA, IRB Common Rule, NIST
AI RMF, ADA, Section 508, and Civil Rights Title VI/IX. It also scores five
ethics dimensions: fairness, privacy, accountability, transparency, and
institutional policy. The toolkit covers 8 use cases, 25 checkpoints, and 12
regulatory and ethics dimensions.

## Architecture

RAISE is organized as three rings:

- Inventory (live): register and track every AI activity.
- Verify (live): run automated checks on uploaded data.
- Govern (roadmap): institution-wide oversight and reporting.

## Features

- Quick Add: describe an activity in one sentence and receive a use case, risk
  flags, and checkpoints.
- Verify Dataset: upload one CSV and run Personal Info Scan, FERPA Compliance,
  Data Classification, and Bias Audit.
- Personal Info Cleanup: redact personal information from an uploaded file.
- Anonymous Grading Mode: hide student identifiers during grading.
- Grading Prompt Generator: build a grading prompt from a rubric.
- Draft Checkpoints: pre-fill checkpoint answers for review.
- Tool Insights: compliance guidance for common software tools.
- Use Cases library: reference for the supported activity types.
- Discussion threads: per-checkpoint comments between collaborators.

## Status

Prototype. Demo data only. Not connected to live student records. Live at
raise-toolkit.vercel.app, gated to USF email addresses.

## Demo data

The demo data is synthetic. The scripts in sample_data/ generate it. They use
reserved identifier ranges: 900-prefix numbers, the .invalid TLD reserved by RFC
2606, and 555-01xx phone numbers. No real personal information is present. The
admissions dataset seeds disparate impact on purpose, so the bias audit has
something to detect. The reported 0.356 disparate impact ratio shows that
detection works. It is not a finding about any real admissions process.

## License

All rights reserved. See LICENSE. Published for demonstration only, not licensed
for reuse.
