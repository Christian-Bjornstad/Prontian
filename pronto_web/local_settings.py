"""Explicit local HTTP settings. The launcher binds exclusively to loopback."""

from . import settings as base

# Django reads uppercase module attributes. Copy the complete base explicitly,
# then override only workstation HTTP settings below.
globals().update({name: value for name, value in vars(base).items() if name.isupper()})

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
PRONTO_DEMO_ENABLED = False
PRONTO_REQUIRE_INITIALS = False

# Public references stay outside Git/static files and are served after login.
PRONTO_IGV_REFERENCE_FILES = dict(base.PRONTO_IGV_REFERENCE_FILES)
PRONTO_IGV_REFERENCES = {build: dict(pair) for build, pair in base.PRONTO_IGV_REFERENCES.items()}
for build in ("GRCh37", "GRCh38"):
    fasta = base.BASE_DIR / ".local-web" / "references" / f"{build}.fa"
    index = fasta.with_suffix(".fa.fai")
    if fasta.is_file() and index.is_file() and not fasta.is_symlink() and not index.is_symlink():
        PRONTO_IGV_REFERENCE_FILES.setdefault(build, {"fasta": str(fasta), "index": str(index)})
    if build in PRONTO_IGV_REFERENCE_FILES and not any(PRONTO_IGV_REFERENCES[build].values()):
        PRONTO_IGV_REFERENCES[build] = {
            "fastaURL": f"/igv/references/{build}/fasta/",
            "indexURL": f"/igv/references/{build}/index/",
        }

PRONTO_WORKING_DRAFTS = True
