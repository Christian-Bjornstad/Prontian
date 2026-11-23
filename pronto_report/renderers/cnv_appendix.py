"""Build the MOL appendix from declared CNV assets and source page numbers."""

from io import BytesIO

from reportlab.platypus import Image, PageBreak, Spacer


def _standard_overview(asset):
    """Identify the documented overview family used for the page 2/4/5 preset."""
    return asset["mediaType"] == "application/pdf" and str(asset["name"]).casefold().endswith(
        "_cnv_overview_plots.pdf"
    )


def cnv_appendix_assets(report):
    """Use the imported CNV role, with the standard filename as a legacy fallback."""
    return tuple(
        asset
        for asset in report.attachments
        if asset["mediaType"] in {"application/pdf", "image/png", "image/jpeg"}
        and (
            _standard_overview(asset)
            or str(asset.get("description", "")).strip().casefold() == "cnv"
        )
    )


def appendix_story(report, plot_images, width, height):
    """Fit the standard pages by position; label every plot by its source.

    Input images must already have passed the declared-asset hash check. An
    alternate or multiple CNV sources are shown in full in source order.
    """
    from .report_pdf import _heading, _paragraph

    sources = [
        (asset, plot_images[str(asset["assetId"])])
        for asset in cnv_appendix_assets(report)
        if plot_images.get(str(asset["assetId"]))
    ]
    if not sources:
        return [
            PageBreak(),
            _heading("CNV appendix unavailable"),
            _paragraph("No imported CNV plot pages are available."),
        ]

    def panel(asset, pages, index, available_height):
        heading = _heading(f"{asset['name']} — source page {index + 1}")
        _, heading_height = heading.wrap(width - 12, available_height)
        image = Image(BytesIO(pages[index][1]))
        image._restrictSize(width - 12, available_height - heading_height - 16)
        image.hAlign = "CENTER"
        return [heading, image]

    asset, pages = sources[0]
    if len(sources) == 1 and _standard_overview(asset) and len(pages) == 9:
        return [
            PageBreak(),
            *panel(asset, pages, 1, height - 8),
            PageBreak(),
            *panel(asset, pages, 3, (height - 14) / 2),
            Spacer(1, 8),
            *panel(asset, pages, 4, (height - 14) / 2),
        ]

    return [
        flow
        for asset, pages in sources
        for index in range(len(pages))
        for flow in [PageBreak(), *panel(asset, pages, index, height - 8)]
    ]
