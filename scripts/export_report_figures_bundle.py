#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
import shutil
import tempfile
import zipfile
from pathlib import Path


FIGURE_RE = re.compile(r"^!\[(.*?)\]\((.+?)\)\s*$")
LABEL_RE = re.compile(r"^Hình\s+([A-Za-z0-9.]+)\.\s*(.*)$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bundle all report figures into a single ZIP with figure-numbered filenames."
    )
    parser.add_argument(
        "--input",
        default="BAO_CAO_BREASTCARE_MINT.md",
        help="Markdown report path.",
    )
    parser.add_argument(
        "--output",
        default="HINH_BAO_CAO_BREASTCARE_MINT.zip",
        help="Output ZIP path.",
    )
    return parser.parse_args()


def parse_figures(markdown_path: Path) -> list[dict[str, str]]:
    figures: list[dict[str, str]] = []
    for line in markdown_path.read_text(encoding="utf-8").splitlines():
        match = FIGURE_RE.match(line.strip())
        if not match:
            continue
        caption = match.group(1).strip()
        rel_path = match.group(2).strip()
        label_match = LABEL_RE.match(caption)
        if label_match:
            figure_no = label_match.group(1).strip()
            title = label_match.group(2).strip()
        else:
            figure_no = f"UNNUMBERED_{len(figures) + 1}"
            title = caption
        figures.append(
            {
                "figure_no": figure_no,
                "caption": caption,
                "title": title,
                "path": rel_path,
            }
        )
    return figures


def safe_figure_stem(figure_no: str) -> str:
    normalized = figure_no.replace(".", "_")
    normalized = re.sub(r"[^A-Za-z0-9_]+", "_", normalized)
    return f"Hinh_{normalized}"


def write_manifest(bundle_dir: Path, figures: list[dict[str, str]]) -> None:
    csv_path = bundle_dir / "DANH_MUC_HINH.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["STT", "So_hinh", "Ten_file", "Caption", "Nguon_goc"])
        for idx, fig in enumerate(figures, start=1):
            writer.writerow(
                [
                    idx,
                    fig["figure_no"],
                    fig["bundle_name"],
                    fig["caption"],
                    fig["path"],
                ]
            )

    md_path = bundle_dir / "DANH_MUC_HINH.md"
    lines = [
        "# DANH MUC HINH BAO CAO",
        "",
        f"Tong so hinh: {len(figures)}",
        "",
        "| STT | So hinh | Ten file | Caption | Nguon goc |",
        "|---:|---|---|---|---|",
    ]
    for idx, fig in enumerate(figures, start=1):
        lines.append(
            f"| {idx} | {fig['figure_no']} | `{fig['bundle_name']}` | {fig['caption']} | `{fig['path']}` |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    txt_path = bundle_dir / "README.txt"
    txt_path.write_text(
        "\n".join(
            [
                "GOI HINH BAO CAO BREASTCARE MINT",
                "",
                f"Tong so hinh: {len(figures)}",
                "Tat ca hinh da duoc doi ten theo so hinh trong bao cao.",
                "Vi du: Hinh_2_1.png, Hinh_3_3.png, Hinh_PL4_12.png",
                "",
                "Xem them danh muc chi tiet trong DANH_MUC_HINH.csv hoac DANH_MUC_HINH.md",
                "",
            ]
        ),
        encoding="utf-8",
    )


def zip_directory(source_dir: Path, output_path: Path) -> None:
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir():
                continue
            zf.write(path, arcname=str(path.relative_to(source_dir)))


def main() -> int:
    args = parse_args()
    markdown_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    root_dir = markdown_path.parent

    figures = parse_figures(markdown_path)
    if not figures:
        raise SystemExit("No figures found in the Markdown report.")

    with tempfile.TemporaryDirectory(prefix="report_figures_") as tmp:
        bundle_dir = Path(tmp) / "HINH_BAO_CAO_BREASTCARE_MINT"
        figures_dir = bundle_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        for fig in figures:
            source = (root_dir / fig["path"]).resolve()
            if not source.exists():
                raise FileNotFoundError(f"Missing figure source: {fig['path']}")
            bundle_name = f"{safe_figure_stem(fig['figure_no'])}{source.suffix.lower()}"
            shutil.copyfile(source, figures_dir / bundle_name)
            fig["bundle_name"] = f"figures/{bundle_name}"

        write_manifest(bundle_dir, figures)

        if output_path.exists():
            output_path.unlink()
        zip_directory(bundle_dir, output_path)

    print(f"Exported figure bundle: {output_path}")
    print(f"Total figures: {len(figures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
