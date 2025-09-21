import os
import sys
from dotenv import find_dotenv, load_dotenv

def parse_font_style(style_str):
    return "".join(c for c in str(style_str).upper() if c in 'BIU')
def parse_color(config, prefix):
    return (int(config.get(f'{prefix}_R', 0)), int(config.get(f'{prefix}_G', 0)), int(config.get(f'{prefix}_B', 0)))
def parse_bool(value):
    return str(value).lower() in ('true', '1', 't', 'y', 'yes')

def load_config():
    env_path = find_dotenv(raise_error_if_not_found=False)
    if not env_path: 
        print("❌ Error: .env file not found.", file=sys.stderr)
        sys.exit(1)
    load_dotenv(env_path)

    config = {
        "csv_files": [p.strip() for p in os.getenv("CSV_FILES", "").split(',') if p.strip()],
        "author": os.getenv("AUTHOR_NAME", "Unknown Author"),
        "version": os.getenv("REPORT_VERSION", "1.0")
    }
    if not config["csv_files"]: 
        print("❌ Error: CSV_FILES not set in .env file.", file=sys.stderr)
        sys.exit(1)

    style_configs = {
        "cover_bg_color": ("color", 'PDF_COVER_BG_COLOR'), "cover_bg_image": ("str", "PDF_COVER_BG_IMAGE"),
        "cover_title_font": ("font", "PDF_COVER_TITLE"), "cover_title_color": ("color", 'PDF_COVER_TITLE_FONT_COLOR'), "cover_title_justification": ("str", "PDF_COVER_TITLE_JUSTIFICATION", "C"),
        "cover_subtitle_font": ("font", "PDF_COVER_SUBTITLE"), "cover_subtitle_color": ("color", 'PDF_COVER_SUBTITLE_FONT_COLOR'), "cover_subtitle_justification": ("str", "PDF_COVER_SUBTITLE_JUSTIFICATION", "C"),

        "header_enabled": ("bool", "PDF_HEADER_ENABLED", "True"), "header_logo": ("str", "PDF_HEADER_LOGO"), "header_layout": ("str", "PDF_HEADER_LAYOUT", "single-line"),
        "header_text": ("str", "PDF_HEADER_TEXT"), "header_text_align": ("str", "PDF_HEADER_TEXT_ALIGN", "L"),
        "header_phone": ("str", "PDF_HEADER_PHONE"), "header_phone_align": ("str", "PDF_HEADER_PHONE_ALIGN", "L"),

        "footer_enabled": ("bool", "PDF_FOOTER_ENABLED", "True"), "footer_logo": ("str", "PDF_FOOTER_LOGO"), "footer_layout": ("str", "PDF_FOOTER_LAYOUT", "single-line"),
        "footer_text": ("str", "PDF_FOOTER_TEXT"), "footer_text_align": ("str", "PDF_FOOTER_TEXT_ALIGN", "R"),
        "footer_page_num_align": ("str", "PDF_FOOTER_PAGE_NUM_ALIGN", "C"),

        "draft_watermark_enabled": ("bool", "PDF_DRAFT_WATERMARK_ENABLED", "False"), "draft_watermark_text": ("str", "PDF_DRAFT_WATERMARK_TEXT", "DRAFT"),
        "draft_watermark_color": ("color", 'PDF_DRAFT_WATERMARK_COLOR'),

        "toc_title_font": ("font", "PDF_TOC_TITLE"), "toc_title_color": ("color", "PDF_TOC_TITLE_FONT_COLOR"),
        "toc_entry_font": ("font", "PDF_TOC_ENTRY"), "toc_entry_color": ("color", "PDF_TOC_ENTRY_FONT_COLOR"),

        "section_title_font": ("font", "PDF_SECTION_TITLE"), "section_title_color": ("color", "PDF_SECTION_TITLE_FONT_COLOR"), "section_title_justification": ("str", "PDF_SECTION_TITLE_JUSTIFICATION", "L"),
        "chart_title_font": ("font", "PDF_CHART_TITLE"), "chart_title_color": ("color", "PDF_CHART_TITLE_FONT_COLOR"), "chart_title_justification": ("str", "PDF_CHART_TITLE_JUSTIFICATION", "L"),
        "table_title_font": ("font", "PDF_TABLE_TITLE"), "table_title_color": ("color", "PDF_TABLE_TITLE_FONT_COLOR"), "table_title_justification": ("str", "PDF_TABLE_TITLE_JUSTIFICATION", "L"),
        "body_font": ("font", "PDF_BODY"), "body_color": ("color", "PDF_BODY_FONT_COLOR"), "body_justification": ("str", "PDF_BODY_JUSTIFICATION", "L"),
        "bucket_name_style": ("style", "PDF_BUCKET_NAME_STYLE"),

        "chart_style": ("str", "CHART_STYLE", "seaborn-v0_8-darkgrid"),
        "chart_title_fontsize": ("int", "CHART_TITLE_FONTSIZE", 14),
        "chart_label_fontsize": ("int", "CHART_LABEL_FONTSIZE", 10),
        # --- DEFINITIVE FIX: Added the missing entry for chart_xaxis_rotation ---
        "chart_xaxis_rotation": ("int", "CHART_XAXIS_ROTATION", 45),
    }

    for key, (kind, prefix, *default) in style_configs.items():
        d = default[0] if default else None
        if kind == "color": config[key] = parse_color(os.environ, prefix)
        elif kind == "font": config[key] = (os.getenv(f"{prefix}_FONT_FAMILY", "Helvetica"), parse_font_style(os.getenv(f"{prefix}_FONT_STYLE", "B" if "TITLE" in prefix.upper() else "")), int(os.getenv(f"{prefix}_FONT_SIZE", 12)))
        elif kind == "str": config[key] = os.getenv(prefix, d)
        elif kind == "bool": config[key] = parse_bool(os.getenv(prefix, d))
        elif kind == "style": config[key] = parse_font_style(os.getenv(prefix, "B"))
        elif kind == "int": config[key] = int(os.getenv(prefix, d))
        elif kind == "float": config[key] = float(os.getenv(prefix, d))

    return config