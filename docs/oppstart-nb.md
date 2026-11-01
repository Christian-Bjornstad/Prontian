# Starte nettleserarbeidsflaten lokalt

Den anbefalte inngangen er [Prontian desktop](desktop-app.md), som styrer
databasevalg, backup og lokal WSGI-server. Denne guiden gjelder den separate
utviklingskommandoen `scripts/start_web.py` og dens eldre `.local-web/config.json`.
Den kommandoen bruker Djangos utviklingsserver og er for lokal utprøving.

Etter installasjon av Python-avhengighetene:

```powershell
.\.venv\Scripts\python.exe scripts\start_web.py --setup-user ditt-brukernavn
```

Velg passord i terminalen. Dette oppretter en vanlig leser/vurderer med tilgang
til rapporter som finnes ved opprettelse, ikke en installasjonsadministrator.
Åpne lokaladressen som skrives i terminalen. Senere starter du uten brukerflagget:

```powershell
.\.venv\Scripts\python.exe scripts\start_web.py
```

Behold terminalen åpen; stopp med Ctrl+C. En annen port kan velges med
`--port 8771`. `--database <sti>` krever en eksisterende fil og husker valget.
`--check` kjører oppsett og migreringer uten server. Denne eldre kommandoen er
har også nøkkelvern og backup før ventende migreringer, men bruker ikke hele
oppsettsflyten til DesktopRuntime. Bruk desktop og
[driftsveiledningen](operations.md) til oppgradering og reell drift.

PDFium håndterer PDF-plott. Bruk egen konto; vurdering og eksport tilskrives
innlogget bruker. Se [revisjonsflyt](report-review-workspace.md),
[PDF og figurer](integrated-review.md) og [IGV-oppsett](igv-alignment-operations.md).
