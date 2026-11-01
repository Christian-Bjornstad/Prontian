# Source and acknowledgements

Prontian (pronto + Christian) is maintained by Christian Bjørnstad. This
repository starts from the desktop application at commit `b1a41f1` of
Christian-Bjornstad/PRONTO on 2026-11-01 and develops it as an independent
repository. It is derived from [InPreD/PRONTO](https://github.com/InPreD/PRONTO).
The original copyright notices and GNU GPL version 3 in [LICENSE](LICENSE)
remain applicable. Independent repository status does not erase source history
or change the license.

The original PPTX command, its configuration, Office templates, transit forms,
historical Word logs and Docker Hub publication workflow are excluded from
Prontian. They remain available in the original project. The local app,
review contracts, adapters, HTML/PDF renderers, migrations and tests are retained.

`pronto_*` package names, `reports_*` database tables, environment variables,
schema identifiers and existing configuration paths are retained deliberately
for compatibility. They are internal identifiers, not separate applications.

The bundled IGV distribution retains its upstream license under
`pronto_report/static/igv/`. The P application artwork was generated for the
desktop application and is reused for Prontian. It is not an institutional logo.

The retained OUS fixture was already approved as public test material in the
source project. See [fixture policy](docs/fixture-and-privacy-policy.md).
New examples created by `scripts/create_desktop_example.py` and the benchmark
are synthetic. No production database, account file, key, raw alignment or
local export belongs in this repository.
