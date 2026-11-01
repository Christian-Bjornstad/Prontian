# Public fixtures and private operational data

The retained integration fixture is
`test_data/ous/251114_A02134_0115_BHCJCKDRX7_TSO_500_LocalApp_postprocessing_results`.
It was already owner-approved as public material in the source project baseline
`50cd812`. Prontian copies only its tracked inputs, with no local additions.
See [fixture mapping](report-data-fixture.md) for the exact adapter assertions.
Git attributes preserve source bytes and trailing empty TSV cells; code whitespace
rules must not rewrite a fixture's data columns.

Unused historical HUS/control fixtures, `.DS_Store` files and generated PPTX
output are excluded. Browser alignment fixtures under
`pronto/tests/reporting/browser/fixtures` are the retained synthetic source
project fixtures used for IGV tests; their targeted Git-ignore exception does
not permit production alignments elsewhere.

`scripts/create_desktop_example.py` generates invented sample tables and plots
in a new directory. `scripts/benchmark_discovery.py` generates temporary synthetic
discovery-only inputs and removes them afterward. Synthetic demo generators
create invented report data without copying production records.

## Never commit

Patient records, databases, keys, credentials, bootstrap accounts, production
alignments, reference genomes, local configuration, unrestricted logs and report
exports stay outside Git. Ignoring a file is a guard, not a content classification.
Check filenames, text, embedded document properties and binary metadata before
staging. Do not upload sensitive test logs as public CI artifacts.

## Adding a fixture

Prefer a small deterministic synthetic fixture. Record its generator/source,
why it is public, which behavior requires it, expected derivatives and approval
by the repository owner or designated data steward. Existing approval does not
extend to a new file added to the same directory. Patient data is never an
acceptable public fixture.

Before pushing inspect `git diff --cached --name-status`, `git diff --cached`
and `git status --short`. Explain binary purpose/provenance in the change.
If inappropriate data has already been pushed, stop distribution and follow
the repository owner's incident/removal process.
