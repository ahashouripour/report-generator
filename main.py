import argparse
import os
from pathlib import Path
import duckdb
import sys
import time
from storage_reporter.config import load_config
from storage_reporter.utils import create_test_files
from storage_reporter.analyzer import DataAnalyzer
from storage_reporter.charting import ChartGenerator
from storage_reporter.reporter import PDFReportGenerator
import argparse


def main():
    parser = argparse.ArgumentParser(description="High-performance storage inventory PDF reporter.")
    parser.add_argument("--test", action="store_true", help="Generate test CSV files and run analysis.")
    parser.add_argument("--rows", type=int, default=10000, help="Approximate rows for test files.")
    parser.add_argument("--files", type=int, default=1, help="Number of multi-project test files.")
    parser.add_argument("--outdir", type=str, default="storage_pdf_report", help="Output directory.")
    parser.add_argument("--threads", type=int, default=max(1, os.cpu_count() or 1), help="CPU threads for DuckDB.")
    parser.add_argument("--memory-limit", type=str, help="Memory limit for DuckDB (e.g., '1GB').")
    args = parser.parse_args()

    output_dir = Path(args.outdir)

    if args.test:
        config = load_config()
        config.update({
            "csv_files": create_test_files(output_dir / "test_data", args.files, args.rows),
            "author": "Test Author",
            "version": "Test v0.1"
        })
    else:
        config = load_config()
        if not all(Path(f).exists() for f in config["csv_files"]):
            print("❌ Error: One or more CSV files in .env do not exist.", file=sys.stderr)
            sys.exit(1)

    # Initialize components
    con = duckdb.connect(database=':memory:')
    con.execute(f"SET threads = {args.threads};")
    if args.memory_limit:
        con.execute(f"SET memory_limit = '{args.memory_limit}';")

    analyzer = DataAnalyzer(con)
    chart_generator = ChartGenerator(config, output_dir / "charts")

    print("\n--- Starting Storage PDF Report Generation ---")
    start_time = time.time()

    report_sections = []

    # Analyze each file individually
    num_sources = len(config["csv_files"])
    has_combined_report = num_sources > 1
    total_steps = num_sources + 1 if has_combined_report else num_sources

    for i, fpath in enumerate(config["csv_files"]):
        print(f"\n[{i+1}/{total_steps}] Analyzing individual file: {fpath}")
        clean_stem = Path(fpath).stem.replace('-', ' ').replace('_', ' ')
        title = f"Analysis for: {clean_stem}"

        aggs = analyzer.analyze_source(fpath)

        # --- DEFINITIVE FIX: Conditional Chart Generation ---
        charts = {}
        total_objects = aggs.get('summary', (0, 0))[0]
        if total_objects > 0:
            charts = chart_generator.generate_all_charts(aggs, Path(fpath).stem)
        else:
            print(f"  --> Skipping chart generation for '{fpath}' as it contains no objects.")

        report_sections.append({'title': title, 'aggs': aggs, 'charts': charts})

    # Analyze all files combined
    if has_combined_report:
        print(f"\n[{total_steps}/{total_steps}] Analyzing all files combined...")
        title = "Combined Analysis of All Files"
        aggs = analyzer.analyze_source(config["csv_files"])
        charts = chart_generator.generate_all_charts(aggs, "combined")
        report_sections.append({'title': title, 'aggs': aggs, 'charts': charts})

    # Assemble the PDF
    print("\nAssembling PDF document...")
    pdf_generator = PDFReportGenerator(config, report_sections, output_dir)
    pdf_generator.create_report()

    elapsed = time.time() - start_time
    print(f"\n--- Report Generation Complete in {elapsed:.2f} seconds ---")
    print(f"✅ PDF Report saved to: {pdf_generator.get_final_path()}")

if __name__ == "__main__":
    main()