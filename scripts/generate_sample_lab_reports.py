from __future__ import annotations

from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


FEATURE_ORDER = [
    ("Mean Radius", "mean_radius"),
    ("Mean Texture", "mean_texture"),
    ("Mean Perimeter", "mean_perimeter"),
    ("Mean Area", "mean_area"),
    ("Mean Smoothness", "mean_smoothness"),
    ("Mean Compactness", "mean_compactness"),
    ("Mean Concavity", "mean_concavity"),
    ("Mean Concave Points", "mean_concave_points"),
    ("Mean Symmetry", "mean_symmetry"),
    ("Mean Fractal Dimension", "mean_fractal_dimension"),
    ("Radius Error", "radius_error"),
    ("Texture Error", "texture_error"),
    ("Perimeter Error", "perimeter_error"),
    ("Area Error", "area_error"),
    ("Smoothness Error", "smoothness_error"),
    ("Compactness Error", "compactness_error"),
    ("Concavity Error", "concavity_error"),
    ("Concave Points Error", "concave_points_error"),
    ("Symmetry Error", "symmetry_error"),
    ("Fractal Dimension Error", "fractal_dimension_error"),
    ("Worst Radius", "worst_radius"),
    ("Worst Texture", "worst_texture"),
    ("Worst Perimeter", "worst_perimeter"),
    ("Worst Area", "worst_area"),
    ("Worst Smoothness", "worst_smoothness"),
    ("Worst Compactness", "worst_compactness"),
    ("Worst Concavity", "worst_concavity"),
    ("Worst Concave Points", "worst_concave_points"),
    ("Worst Symmetry", "worst_symmetry"),
    ("Worst Fractal Dimension", "worst_fractal_dimension"),
]

BENIGN = {
    "mean_radius": 13.54,
    "mean_texture": 14.36,
    "mean_perimeter": 87.46,
    "mean_area": 566.3,
    "mean_smoothness": 0.09779,
    "mean_compactness": 0.08129,
    "mean_concavity": 0.06664,
    "mean_concave_points": 0.04781,
    "mean_symmetry": 0.1885,
    "mean_fractal_dimension": 0.05766,
    "radius_error": 0.2699,
    "texture_error": 0.7886,
    "perimeter_error": 2.058,
    "area_error": 23.56,
    "smoothness_error": 0.008462,
    "compactness_error": 0.0146,
    "concavity_error": 0.02387,
    "concave_points_error": 0.01315,
    "symmetry_error": 0.0198,
    "fractal_dimension_error": 0.0023,
    "worst_radius": 15.11,
    "worst_texture": 19.26,
    "worst_perimeter": 99.7,
    "worst_area": 711.2,
    "worst_smoothness": 0.144,
    "worst_compactness": 0.1773,
    "worst_concavity": 0.239,
    "worst_concave_points": 0.1288,
    "worst_symmetry": 0.2977,
    "worst_fractal_dimension": 0.07259,
}

MALIGNANT = {
    "mean_radius": 17.99,
    "mean_texture": 10.38,
    "mean_perimeter": 122.8,
    "mean_area": 1001.0,
    "mean_smoothness": 0.1184,
    "mean_compactness": 0.2776,
    "mean_concavity": 0.3001,
    "mean_concave_points": 0.1471,
    "mean_symmetry": 0.2419,
    "mean_fractal_dimension": 0.07871,
    "radius_error": 1.095,
    "texture_error": 0.9053,
    "perimeter_error": 8.589,
    "area_error": 153.4,
    "smoothness_error": 0.006399,
    "compactness_error": 0.04904,
    "concavity_error": 0.05373,
    "concave_points_error": 0.01587,
    "symmetry_error": 0.03003,
    "fractal_dimension_error": 0.006193,
    "worst_radius": 25.38,
    "worst_texture": 17.33,
    "worst_perimeter": 184.6,
    "worst_area": 2019.0,
    "worst_smoothness": 0.1622,
    "worst_compactness": 0.6656,
    "worst_concavity": 0.7119,
    "worst_concave_points": 0.2654,
    "worst_symmetry": 0.4601,
    "worst_fractal_dimension": 0.1189,
}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def mutate_values(base: dict[str, float], rng: Random, intensity: float) -> dict[str, float]:
    out = {}
    for key, value in base.items():
        factor = 1 + rng.uniform(-intensity, intensity)
        if value < 1:
            factor = 1 + rng.uniform(-intensity * 0.6, intensity * 0.6)
        out[key] = round(value * factor, 6)
    return out


def format_value(value: float) -> str:
    if value >= 100:
        return f"{value:.1f}"
    if value >= 10:
        return f"{value:.2f}"
    if value >= 1:
        return f"{value:.3f}"
    return f"{value:.6f}".rstrip("0").rstrip(".")


def draw_report(draw: ImageDraw.ImageDraw, values: dict[str, float], seed: int, patient_label: str, report_title: str) -> None:
    rng = Random(seed)
    title_font = load_font(36, bold=True)
    body_font = load_font(22)
    small_font = load_font(18)

    width = 1700
    draw.rounded_rectangle((40, 40, width - 40, 230), radius=22, outline=(40, 84, 116), width=3, fill=(248, 252, 255))
    draw.text((70, 70), "BREASTCARE MINT DIAGNOSTIC REPORT", fill=(11, 35, 62), font=title_font)
    draw.text((70, 125), report_title, fill=(34, 87, 125), font=body_font)
    draw.text((70, 165), f"Patient ID: {patient_label}", fill=(68, 85, 102), font=small_font)
    draw.text((520, 165), f"Report Seed: {seed}", fill=(68, 85, 102), font=small_font)
    draw.text((760, 165), "Specimen: Breast FNA Cytology", fill=(68, 85, 102), font=small_font)
    draw.text((1180, 165), "Units: Standardized numeric values", fill=(68, 85, 102), font=small_font)

    draw.rounded_rectangle((40, 260, width - 40, 1580), radius=20, outline=(90, 120, 140), width=2, fill=(255, 255, 255))

    left_x = 90
    right_x = 870
    y = 320
    row_h = 78

    headers = [("Feature", 90), ("Value", 580), ("Feature", 870), ("Value", 1360)]
    for text, x in headers:
        draw.text((x, 280), text, fill=(24, 61, 89), font=body_font)
    draw.line((80, 315, width - 80, 315), fill=(170, 190, 205), width=2)

    half = len(FEATURE_ORDER) // 2
    for idx in range(half):
        row_y = y + idx * row_h
        if idx % 2 == 0:
            draw.rounded_rectangle((65, row_y - 12, width - 65, row_y + 48), radius=10, fill=(248, 251, 253))
        l_label, l_key = FEATURE_ORDER[idx]
        r_label, r_key = FEATURE_ORDER[idx + half]
        draw.text((left_x, row_y), l_label, fill=(28, 43, 58), font=body_font)
        draw.text((580, row_y), format_value(values[l_key]), fill=(10, 84, 52), font=body_font)
        draw.text((right_x, row_y), r_label, fill=(28, 43, 58), font=body_font)
        draw.text((1360, row_y), format_value(values[r_key]), fill=(10, 84, 52), font=body_font)

    draw.rounded_rectangle((40, 1610, width - 40, 1810), radius=18, outline=(203, 210, 216), width=2, fill=(251, 251, 251))
    notes = [
        "Clinical note: values should be reviewed by a physician before use.",
        "This sheet is for AI demo and OCR extraction testing only.",
        "If any value is unclear in the image, manual verification is required.",
    ]
    note_y = 1650
    for note in notes:
        draw.text((70, note_y), f"- {note}", fill=(82, 90, 98), font=small_font)
        note_y += 42

    if rng.random() < 0.7:
        stamp_color = (180, 30, 45, 140)
        draw.rounded_rectangle((1250, 70, 1560, 140), radius=10, outline=stamp_color[:3], width=4)
        draw.text((1285, 88), "LAB VERIFIED", fill=stamp_color[:3], font=load_font(30))


def add_camera_effects(img: Image.Image, rng: Random, variant: int) -> Image.Image:
    canvas = Image.new("RGB", (1900, 2000), (236, 239, 242))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((15, 15, img.size[0] - 15, img.size[1] - 15), radius=24, fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))

    angle = rng.uniform(-4.5, 4.5)
    if variant in {3, 7}:
        angle = rng.uniform(-7.5, 7.5)

    paper = img.convert("RGBA")
    paper = paper.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255, 0))
    shadow = shadow.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0))

    px = rng.randint(90, 180)
    py = rng.randint(70, 120)
    canvas.paste(shadow, (px + 14, py + 18), shadow)
    canvas.paste(paper, (px, py), paper)

    if variant in {2, 5, 8}:
        overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
        o = ImageDraw.Draw(overlay)
        o.polygon([(0, 0), (520, 0), (260, 420)], fill=(255, 255, 255, 55))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    if variant in {4, 9}:
        canvas = canvas.filter(ImageFilter.GaussianBlur(0.6))

    return canvas


def main() -> None:
    out_dir = Path("frontend/assets/demo-lab-reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = Random(42)

    configs = [
        ("Benign-style report A", BENIGN, 0.04),
        ("Malignant-style report A", MALIGNANT, 0.04),
        ("Benign-style report B", BENIGN, 0.06),
        ("Malignant-style report B", MALIGNANT, 0.06),
        ("Benign-style report C", BENIGN, 0.05),
        ("Malignant-style report C", MALIGNANT, 0.05),
        ("Benign-style report D", BENIGN, 0.07),
        ("Malignant-style report D", MALIGNANT, 0.07),
        ("Benign-style report E", BENIGN, 0.08),
        ("Malignant-style report E", MALIGNANT, 0.08),
    ]

    for idx, (title, base_values, intensity) in enumerate(configs, start=1):
        values = mutate_values(base_values, rng, intensity)
        report = Image.new("RGB", (1700, 1850), (255, 255, 255))
        draw = ImageDraw.Draw(report)
        draw_report(draw, values, seed=1000 + idx, patient_label=f"BCM-{1000 + idx}", report_title=title)
        final = add_camera_effects(report, rng, idx)
        final.save(out_dir / f"sample-lab-report-{idx:02d}.png", quality=95)

    print(f"Generated 10 sample lab report images in {out_dir}")


if __name__ == "__main__":
    main()
