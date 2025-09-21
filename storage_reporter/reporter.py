from datetime import datetime
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from .utils import format_bytes, DynamicExplanations

class PDF(FPDF):
    def __init__(self, config, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    # --- DEFINITIVE FIX FOR HEADER ALIGNMENT ---
    def header(self):
        if not self.config['header_enabled'] or self.page_no() == 1:
            return

        self.set_font('Helvetica', '', 8)
        self.set_text_color(0, 0, 0)

        layout = self.config.get('header_layout', 'single-line')
        logo_path = self.config.get('header_logo')

        y_start = self.t_margin

        if layout == 'multi-line':
            self.set_y(y_start)
            if logo_path and Path(logo_path).exists():
                self.image(logo_path, x=10, y=y_start, h=9)
                self.set_y(y_start + 9 + 2) # Position cursor below logo

            self.cell(w=0, h=5, text=self.config.get('header_text', ''), align=self.config.get('header_text_align', 'L'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            if self.config.get('header_phone', '').strip():
                self.cell(w=0, h=5, text=self.config.get('header_phone'), align=self.config.get('header_phone_align', 'L'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        else: # single-line layout
            line_height = 10
            self.set_y(y_start)

            text_start_x = self.l_margin
            if logo_path and Path(logo_path).exists():
                self.image(logo_path, x=10, y=y_start, h=9)
                text_start_x = 30 # Indent text to the right of the logo

            text_parts = [self.config.get('header_text'), self.config.get('header_phone')]
            full_header_text = " | ".join(filter(None, [part.strip() for part in text_parts if part]))

            align = self.config.get('header_text_align', 'L')
            text_width = self.get_string_width(full_header_text)

            if align == 'C':
                # Center the text in the space available between the start position and the right margin
                available_width = self.w - text_start_x - self.r_margin
                x_pos = text_start_x + (available_width - text_width) / 2
            elif align == 'R':
                x_pos = self.w - self.r_margin - text_width
            else: # 'L'
                x_pos = text_start_x

            self.set_x(x_pos)
            self.cell(w=text_width, h=line_height, text=full_header_text, align='L')

        # Draw line below all content and set cursor for the main body
        final_y = self.get_y() + 3 if layout == 'multi-line' else y_start + line_height
        self.line(10, final_y, 200, final_y)
        self.set_y(final_y + 3)

    def footer(self):
        # Draw the standard footer content first
        if self.config['footer_enabled'] and self.page_no() > 1:
            with self.local_context():
                self.set_y(-20)
                layout, logo_path = self.config.get('footer_layout', 'single-line'), self.config.get('footer_logo')
                if layout == 'multi-line':
                    if logo_path and Path(logo_path).exists(): 
                        self.image(logo_path, x=self.w / 2 - 10, y=self.get_y(), h=7)
                        self.ln(8)
                    self.set_font('Helvetica', 'I', 8)
                    self.set_text_color(128)
                    self.cell(w=0, h=5, text=f'Page {self.page_no()}', align=self.config.get('footer_page_num_align', 'C'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    self.set_font('Helvetica', '', 8)
                    self.set_text_color(0,0,0)
                    self.cell(w=0, h=5, text=self.config.get('footer_text', ''), align=self.config.get('footer_text_align', 'C'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                else:
                    if logo_path and Path(logo_path).exists(): self.image(logo_path, x=10, y=self.get_y() + 2, h=5)
                    self.set_y(-15)
                    self.set_font('Helvetica', 'I', 8)
                    self.set_text_color(128)
                    self.cell(w=0, h=10, text=f'Page {self.page_no()}', border=0, align=self.config.get('footer_page_num_align', 'C'))
                    if self.config.get('footer_text'):
                        self.set_y(-15)
                        self.set_font('Helvetica', '', 8)
                        self.set_text_color(0,0,0)
                        self.cell(w=0, h=10, text=self.config.get('footer_text'), border=0, align=self.config.get('footer_text_align', 'R'))

        # Draw the watermark last, so it's on top of all page content.
        if self.page_no() > 1 and self.config['draft_watermark_enabled']:
            with self.local_context():
                self.set_font('Helvetica', 'B', 50)
                self.set_text_color(*self.config['draft_watermark_color'])
                self.rotate(45, x=self.w/2, y=self.h/2)
                self.text(x=self.w/2 - self.get_string_width(self.config['draft_watermark_text'])/2, y=self.h/2 + 20, text=self.config['draft_watermark_text'])

# ... (The rest of the reporter.py file is unchanged) ...
class PDFReportGenerator:
    def __init__(self, config, report_sections, output_dir): 
        self.config, self.report_sections, self.output_dir = config, report_sections, output_dir
        self.pdf = PDF(config)
    def create_report(self):
        self._add_cover_page()
        toc_links = [(section['title'], self.pdf.add_link()) for section in self.report_sections]
        self._add_table_of_contents_page(toc_links)
        for i, section in enumerate(self.report_sections): 
            self.pdf.add_page()
            self.pdf.set_link(toc_links[i][1], page=self.pdf.page_no())
            self._add_section_content_to_pdf(section['title'], section['aggs'], section['charts'])
        self.pdf.output(self.get_final_path())
    def get_final_path(self): 
        return self.output_dir / "Storage_Analysis_Report.pdf"
    def _add_cover_page(self):
        self.pdf.add_page()
        self.pdf.set_auto_page_break(False)
        if all(c is not None for c in self.config['cover_bg_color']): 
            self.pdf.set_fill_color(*self.config['cover_bg_color'])
            self.pdf.rect(0, 0, 210, 297, 'F')
        if self.config['cover_bg_image'] and Path(self.config['cover_bg_image']).exists(): 
            self.pdf.image(self.config['cover_bg_image'], x=0, y=0, w=210)
        self.pdf.set_y(60)
        self.pdf.set_font(*self.config['cover_title_font'])
        self.pdf.set_text_color(*self.config['cover_title_color'])
        self.pdf.multi_cell(w=0, h=15, text='Storage Inventory\nAnalysis Report', align=self.config['cover_title_justification'])
        self.pdf.ln(25)
        self.pdf.set_font(*self.config['cover_subtitle_font'])
        self.pdf.set_text_color(*self.config['cover_subtitle_color'])
        self.pdf.cell(w=0, h=10, text=f"Version: {self.config['version']}", align=self.config['cover_subtitle_justification'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.cell(w=0, h=10, text=f"Author: {self.config['author']}", align=self.config['cover_subtitle_justification'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.cell(w=0, h=10, text=f'Generated: {datetime.now().strftime("%Y-%m-%d")}', align=self.config['cover_subtitle_justification'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.set_auto_page_break(True, margin=15)
        self.pdf.set_text_color(0,0,0)
    def _add_table_of_contents_page(self, toc_links):
        self.pdf.add_page()
        self.pdf.set_font(*self.config['toc_title_font'])
        self.pdf.set_text_color(*self.config['toc_title_color'])
        self.pdf.cell(w=0, h=20, text='Table of Contents', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(10)
        self.pdf.set_font(*self.config['toc_entry_font'])
        self.pdf.set_text_color(*self.config['toc_entry_color'])
        for title, link in toc_links: 
            self.pdf.cell(w=0, h=10, text=title, align='L', link=link, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    def _add_section_content_to_pdf(self, title, aggs, chart_paths):
        self.pdf.start_section(title, level=0)
        self._write_dynamic_title(title, self.config['section_title_font'], self.config['section_title_color'], self.config['section_title_justification'])
        total_objects, total_size = aggs['summary']
        summary_data = [["Metric", "Value"], ["Total Objects", f"{total_objects:,}"], ["Total Storage", format_bytes(total_size)], ["Avg Object Size", format_bytes(total_size/total_objects if total_objects > 0 else 0)]]
        self._write_table_to_pdf("Overall Summary", summary_data)
        df_projects = aggs['top_projects'].copy()
        df_projects['total_size'] = df_projects['total_size'].apply(format_bytes)
        self._write_df_to_pdf("Top 10 Projects by Size", df_projects)
        df_buckets = aggs['top_buckets'].copy()
        df_buckets['total_size'] = df_buckets['total_size'].apply(format_bytes)
        self._write_df_to_pdf("Top 10 Buckets by Size", df_buckets)
        explanations = DynamicExplanations(aggs, title).get_all()
        for chart_title, chart_path in chart_paths.items():
            if self.pdf.get_y() + 120 > self.pdf.h - self.pdf.b_margin: 
                self.pdf.add_page()
            self._write_dynamic_title(chart_title, self.config['chart_title_font'], self.config['chart_title_color'], self.config['chart_title_justification'], h=15)
            explanation = explanations.get(chart_title, "No description available.")
            self.pdf.set_font(*self.config['body_font'])
            self.pdf.set_text_color(*self.config['body_color'])
            self.pdf.multi_cell(w=0, h=5, text=explanation, align=self.config['body_justification'])
            self.pdf.ln(5)
            self.pdf.image(chart_path, w=self.pdf.w - 40)
            self.pdf.ln(5)
    def _write_dynamic_title(self, title, font_config, color_config, justification, h=10):
        original_family, original_style, original_size = font_config
        self.pdf.set_text_color(*color_config)
        available_width = self.pdf.w - self.pdf.l_margin - self.pdf.r_margin
        words = title.split(' ')
        longest_word = max(words, key=len) if words else ""
        current_font_size = original_size
        while current_font_size > 6:
            self.pdf.set_font(original_family, original_style, current_font_size)
            if self.pdf.get_string_width(longest_word) < available_width: 
                break
            current_font_size -= 1
        self.pdf.multi_cell(w=available_width, h=h, text=title, align=justification)
        self.pdf.ln(5)
        self.pdf.set_font(original_family, original_style, original_size)
    def _write_table_to_pdf(self, title, data):
        self._write_dynamic_title(title, self.config['table_title_font'], self.config['table_title_color'], self.config['table_title_justification'], h=15)
        if not data or len(data) < 2: 
            return
        self.pdf.set_font('Helvetica', 'B', 10)
        self.pdf.set_text_color(0,0,0)
        col_widths = self._get_col_widths(data)
        for i, h in enumerate(data[0]): 
            self.pdf.cell(w=col_widths[i], h=10, text=str(h), border=1, align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.pdf.ln()
        self.pdf.set_font('Helvetica', '', 10)
        for row in data[1:]:
            for i, item in enumerate(row):
                style = self.config['bucket_name_style'] if "Buckets" in title and i == 0 else ""
                self.pdf.set_font('Helvetica', style, 10)
                self.pdf.cell(w=col_widths[i], h=10, text=str(item), border=1, align=self.config['body_justification'], new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.pdf.ln()
        self.pdf.ln(10)
    def _get_col_widths(self, data):
        max_widths = [max(self.pdf.get_string_width(str(cell)) for cell in col) for col in zip(*data)]
        total_width = sum(max_widths) + len(max_widths) * 4
        available_width = self.pdf.w - 40
        scale = available_width / total_width if total_width > available_width else 1.0
        return [(w + 4) * scale for w in max_widths]
    def _write_df_to_pdf(self, title, df):
        if not df.empty: self._write_table_to_pdf(title, [df.columns.tolist()] + df.values.tolist())