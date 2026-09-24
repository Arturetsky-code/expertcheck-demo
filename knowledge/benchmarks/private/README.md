# Private Test78 fixture

This directory contains only **encrypted ciphertext chunks** for the real Test78
deterministic Assignment benchmark.

The repository is public. Never commit the plaintext fixture, extracted project-page
text, the 12 source PDFs, or the decryption key.

The encrypted fixture contains:
- the fixed 56-requirement denominator;
- the cached 12-document page corpus;
- the historical encrypted baseline row states (the current audited state is applied separately through the public baseline manifest);
- the count of the two separately audited proven deviations.

GitHub Actions reconstructs the fixture only in the runner workspace using the
repository Actions secret `TEST78_FIXTURE_KEY`.

The workflow output is deliberately non-sensitive:
- before/after counts;
- classification (`NO_CHANGE`, `SINGLE_GAIN`, `REGRESSION`, etc.);
- changed requirement IDs;
- Core25 reason/executor identifiers.

No page text or project snippets are written to public logs or the compact public result artifact.

The current audited baseline is stored separately in
`knowledge/benchmarks/test78_baseline_overrides.json`. This manifest contains only
non-sensitive requirement IDs and categorical state/reason/executor identifiers. It
can supersede historical baseline row states embedded in the encrypted fixture without
requiring the full private corpus to be re-encrypted.

For private diagnostics, the workflow may upload a short-lived **encrypted** review
frontier artifact. Its plaintext is never committed to the repository or written to
the public workflow summary.

## Security / rotation

If the fixture must be replaced:
1. create a new fixed benchmark fixture;
2. gzip and encrypt it with AES-256-CBC + PBKDF2 (200000 iterations) using a new
   high-entropy key;
3. replace the encrypted chunks;
4. rotate `TEST78_FIXTURE_KEY`;
5. update the accepted baseline only after the normal manual evidence audit.
