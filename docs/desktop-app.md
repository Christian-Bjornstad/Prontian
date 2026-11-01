# Prontian – installasjon og daglig bruk

Prontian samler filimport, database og lokal rapportserver i ett programvindu.
Rapportene åpnes i nettleseren etter innlogging. Kildedata og vurderinger lagres
separat; en faglig vurdering overskriver ikke den importerte kildeverdien.

## Installere og starte

Bruk 64-bit Python 3.14. Åpne PowerShell i prosjektmappen:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pronto_desktop
```

PDFium følger Python-avhengighetene og leser PDF-plott. Poppler er en valgfri
reserve, og trenger ikke installeres for vanlig bruk med fungerende PDFium.

Med Python FELLES/Ivanti: kjør `PRONTIAN_INSTALL.cmd`, deretter
`PRONTIAN_START.cmd`. Startfilene åpner det eksisterende FELLES-oppsettet og
kopierer en oppstartskommando som limes inn i Python-vinduet. Med lokal Python
brukes valgt `PRONTO_PYTHON`, prosjektets virtuelle miljø eller Python 3.14.
Behold hele programmappen samlet. `PRONTIAN_SNARVEI.cmd` lager en valgfri
Prontian-snarvei når du kjører den.

Ved en tom installasjon opprettes første administrator i dialogen. Administrator
kan deretter opprette personlige brukerkontoer. Bruk egen konto til import og
vurdering; handlinger knyttes til innlogget bruker. Programkontoer endrer ikke
rettigheter på Windows-/nettverksområdet.

## Eksisterende installasjon

Behold database, datamappe, råarkiv og opprinnelig `secret.key`. Interne filnavn
som `pronto.sqlite3`, `pronto-installation.json` og brukerprofilen under
`%LOCALAPPDATA%\PRONTO` er beholdt med vilje. De skal ikke gis nytt navn.

Kontroller databaseplasseringen i Innstillinger. Manglende/gammel peker kan
gjenopprettes ved å velge den eksisterende filen og riktig datarot. Ved tilgang
nektet må rettighetene rettes; ikke opprett en ny database eller nøkkel.
Se [drift og gjenoppretting](operations.md) før oppgradering.

## Finne og importere en kjøring

1. Åpne **Importer → Kilder**. Velg **Kjøringsdato** og hovedmappen som inneholder
   kjøringsmappene. Skriv `261021`, `20261021`, `2026-10-21` eller full kjørings-ID.
2. Velg **Kontroller filer**. Ved flere kjøringer på datoen velger du riktig ID.
   Søket leser mapper inntil tre nivåer ned og stopper ved kjøringsgrensene.
3. Alternativet **Mapper** lar deg velge én til fem separate kildemapper.
4. Kontroller rapportversjon og CNV-kilde. Automatisk valg bruker tilgjengelig
   QC-grunnlag for prøven, deretter nyere/tidligere pre-QC og rådata.
5. Se gjennom prøveoversikten. Avklar manglende eller konkurrerende kilder og
   eksakt DNA/RNA-kobling. `Create_report=-` krever at prøven velges aktivt;
   negative metadataflagg kan ikke overstyres med vanlig prøvevalg.
6. Velg **Importer valgte**. Hver prøve valideres og arkiveres før rapporten
   opprettes. Avbrudd fjerner ikke prøver som allerede ble fullført.

Kildemappene endres ikke. En identisk import lager ikke en rapportdublett.
Endret kildeinnhold for en eksisterende rapport gir konflikt som må avklares.
Søket er forbedret med lokale mellomlagre og en kildeindeks; importen kontrollerer
fortsatt filene på nytt. Se [målinger](performance.md).

Lag et rent øvingsgrunnlag med:

```powershell
.\.venv\Scripts\python.exe scripts\create_desktop_example.py --output examples\generated\run
```

Velg den nye mappen i Importer og marker DNA-prøven i forhåndsvisningen.
Bruk en separat testdatabase når du øver.

## Rapportarbeid

**Åpne rapporter** starter eller gjenbruker den lokale serveren. Logg inn i
nettleseren. Velg rapport og åpne redigering. Småvarianter, CNV, RNA, QC og
rapporttekst deler samme vurdering. Include/Exclude, klassifisering, IGV-QC og
Report highlight har hver sin betydning. Ekskluderte funn tas ikke med bare
fordi highlight er valgt.

**Save** oppdaterer arbeidskladden. **Finalize** bevarer en endelig revisjon.
**Start new revision** åpner en ny kladd fra en bevart versjon. Ved konflikt
har en annen lagring vunnet; behold lokale endringer før siste versjon lastes.
HTML/PDF-eksport bruker lagret innhold. Eksport kan bevare et øyeblikksbilde og
flytte den aktive kladden videre til neste revisjon.

Se [arbeidsflate og revisjoner](report-review-workspace.md) og
[PDF-formatene](integrated-review.md) for detaljer.

## IGV, backup og avslutning

IGV trenger riktig referansegenom og tilhørende indeks. Lokalt filvalg for
visning sender ikke BAM-filen til serveren. Permanent alignmentlagring er en
egen funksjon, deaktivert uten særskilt oppsett og Linux-støtte.
Se [IGV-drift](igv-alignment-operations.md).

Bruk sikkerhetskopifunksjonen og avtal komplett backup av arkiv, nøkkel og
eventuelle genomfiler i tillegg til SQL. Lukk appen kontrollert etter lagring;
serveren venter på aktive forespørsler. Felles SQLite på nettverksdisk er ikke
verifisert for samtidige skrivere. Se [produksjonsstatus](production-readiness.md).
