# Markdown formatting-only normalization — 2026-10-24

- SIP-1352 and SIP-3756: insert only mandatory blank lines following Markdown headings to pass strict MD022 without changing technical wording.
- `_config.yml`: remove the redundant syntax-highlighter setting because Jekyll already provides its default highlighter. The removed configuration string was misread as a spelling error by the branch-wide spelling gate.
- No new identity aliases, API compatibility layers, authors, governance statuses or licensing claims.
- These two files therefore deliberately differ from their exact original Batch5 SHA-256; the material between headings remains unchanged. Review the diff to confirm that the changes are whitespace only.
- Re-run the site build and the repository checks. Remaining rights, full-corpus and deployment blockers are not waived.
