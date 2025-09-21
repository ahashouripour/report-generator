import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

class DynamicExplanations:
    """Generates data-driven text explanations for charts."""
    def __init__(self, aggs, source_name):
        self.aggs = aggs
        self.source_name = source_name
        self.total_objects, self.total_size = self.aggs.get('summary', (0, 0))

    def get_all(self):
        return {
            "Chart: Storage Dashboard": self.dashboard(),
            "Chart: Top 10 Projects by Size": self.top_projects(),
            "Chart: Top 10 Buckets by Size": self.top_buckets(),
            "Chart: Storage Distribution by Project": self.distribution_by_project(),
            "Chart: File Size Distribution": self.file_size_distribution(),
            "Chart: Cumulative Monthly Storage Growth": self.cumulative_monthly_growth(),
            "Chart: Cumulative Yearly Storage Growth": self.cumulative_yearly_growth(),
        }

    def dashboard(self):
        top_project_df = self.aggs.get('top_projects')
        top_bucket_df = self.aggs.get('top_buckets')
        top_project_text = "No project data available." if top_project_df.empty else f"The largest project is '{top_project_df['project_id'].iloc[0]}'."
        top_bucket_text = "No bucket data available." if top_bucket_df.empty else f"The single largest bucket is '{top_bucket_df['bucket_name'].iloc[0]}'."
        return f"This dashboard provides a high-level summary for '{self.source_name}'. It combines critical metrics into a single view. {top_project_text} {top_bucket_text}"

    def top_projects(self):
        df = self.aggs.get('top_projects')
        if df.empty or self.total_size in [None, 0]: return f"No project data found for '{self.source_name}'."
        name, size = df['project_id'].iloc[0], df['total_size'].iloc[0]
        pct = (size / self.total_size) * 100 if self.total_size > 0 else 0
        return f"This chart aggregates storage for each project, showing the top 10. For '{self.source_name}', '{name}' is the largest, accounting for {format_bytes(size)} ({pct:.1f}% of the total). This view is critical for strategic planning and budget allocation."

    def top_buckets(self):
        df = self.aggs.get('top_buckets')
        if df.empty or self.total_size in [None, 0]: return f"No bucket data found for '{self.source_name}'."
        name, size = df['bucket_name'].iloc[0], df['total_size'].iloc[0]
        pct = (size / self.total_size) * 100 if self.total_size > 0 else 0
        large_bucket_threshold_bytes = 10 * (1024**3)
        concluding_remark = "making it a key target for potential cleanup or data tiering initiatives." if size > large_bucket_threshold_bytes else "which is a manageable size and may not require immediate attention."
        return f"This chart identifies the top 10 largest individual buckets. For '{self.source_name}', '{name}' consumes the most space at {format_bytes(size)} ({pct:.1f}% of the total), {concluding_remark}"

    # --- DEFINITIVE FIX FOR DYNAMIC TEXT ---
    def distribution_by_project(self):
        df = self.aggs.get('distribution_by_project')
        if df.empty:
            return f"No project data found in '{self.source_name}' to create a distribution chart."

        # Check the number of projects to mirror the logic in charting.py
        if len(df) == 1:
            # Generate text for the single-item BAR CHART case
            return (
                "This chart shows the total storage for the single project found in this data source. "
                "Because only one item was detected, a bar chart is used instead of a pie chart for clarity. "
                "This view is critical for understanding the overall storage footprint of this project."
            )
        else:
            # Generate text for the multi-item PIE CHART case
            grouping_text = "all projects are displayed."
            if len(df) > 5:
                grouping_text = "the smallest projects are grouped into an 'Others' category for clarity."

            return (
                f"This pie chart illustrates the proportion of total storage consumed by each project. In this dataset "
                f"of {len(df)} unique projects, {grouping_text} This view is critical for understanding which "
                "teams or applications are the primary drivers of storage costs."
            )

    def file_size_distribution(self):
        df = self.aggs.get('size_distribution')
        if df.empty: return "No file size data could be calculated."
        dom = df.loc[df['object_count'].idxmax()]
        return f"This chart categorizes objects by size. The data in '{self.source_name}' is primarily composed of files in the '{dom['size_category']}' range, with {dom['object_count']:,} objects. This helps understand the nature of the data."

    def cumulative_monthly_growth(self):
        df = self.aggs.get('monthly_growth')
        if df.empty or df['month'].isnull().all(): return "No time-series data was available."
        first, last = df['month'].min().strftime('%Y-%m'), df['month'].max().strftime('%Y-%m')
        return (f"This chart displays the cumulative growth of storage on a month-by-month basis from {first} to {last}. "
                "The upward trend visualizes the rate at which new data is being added, which is useful for observing "
                "short-to-medium term trends and seasonal changes in storage consumption.")

    def cumulative_yearly_growth(self):
        df = self.aggs.get('yearly_growth')
        if df.empty or df['year'].isnull().all(): return "No yearly time-series data was available to plot storage growth."
        first = df['year'].min().strftime('%Y')
        last = df['year'].max().strftime('%Y')
        return (f"This chart displays the cumulative growth of storage on a year-by-year basis from {first} to {last}. "
                "This high-level view is key for understanding the long-term data growth trajectory and for forecasting "
                "future capacity and budget requirements over multiple years.")


def format_bytes(byte_count):
    if byte_count is None or not isinstance(byte_count, (int, float)) or byte_count < 0:
        return "0 B"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB', 5: 'PB'}
    while byte_count >= power and n < len(power_labels) - 1:
        byte_count /= power
        n += 1
    return f"{byte_count:.2f} {power_labels[n]}"

def create_test_files(directory: Path, num_files: int, num_rows: int):
    # (function is unchanged)
    print(f"📝 Generating {num_files + 2} test files with ~{num_rows:,} rows each in '{directory}'...")
    directory.mkdir(parents=True, exist_ok=True)
    generated_paths = []
    headers = ["project_id", "bucket_name", "object_name", "size_bytes", "content_type", "creation_time_utc", "updated_time_utc"]
    empty_filepath = directory / "empty-file.csv"
    generated_paths.append(str(empty_filepath))
    with open(empty_filepath, 'w', newline='', encoding='utf-8') as f: 
        writer = csv.writer(f)
        writer.writerow(headers)
    dominant_project_name = "dominant-project-test"
    single_project_filepath = directory / f"{dominant_project_name}-with-a-very-long_and_unbroken-descriptive-filename-to-test-wrapping.csv"
    generated_paths.append(str(single_project_filepath))
    with open(single_project_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i in range(num_rows):
            size = random.randint(10**9, 10**10) if i > 10 else ""
            writer.writerow([dominant_project_name, f'{dominant_project_name}-main-bucket', 'data.csv', size, 'text/csv', datetime.now().isoformat() + 'Z', datetime.now().isoformat() + 'Z'])
            writer.writerow([dominant_project_name, f'{dominant_project_name}-archive-bucket', 'archive.zip', random.randint(10**8, 10**9), 'application/zip', datetime.now().isoformat() + 'Z', datetime.now().isoformat() + 'Z'])
    for i in range(num_files):
        filepath = directory / f"test-data-part-{i+1}.csv"
        generated_paths.append(str(filepath))
        projects = [f'project-alpha-{i}', f'project-beta-{i}']
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for j in range(num_rows // 2):
                size = int(random.lognormvariate(mu=12, sigma=4) * 1024)
                created = datetime(2022, 1, 1) + timedelta(days=random.randint(0, 365*2))
                writer.writerow([random.choice(projects), f"{random.choice(projects)}-{random.choice(['hot', 'archive'])}", f"data/file_{j}.parquet", size, random.choice(['image/jpeg', 'video/mp4']), created.isoformat() + "Z", (created + timedelta(days=1)).isoformat() + "Z"])
    assets_dir = directory.parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    logo_path = assets_dir / "test_logo.png"
    if not logo_path.exists():
        img = Image.new('RGB', (100, 30), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        try: f = ImageFont.truetype("arial.ttf", 15)
        except IOError: f = ImageFont.load_default()
        d.text((10, 10), "LOGO", font=f, fill=(255, 255, 255))
        img.save(logo_path)
        print(f"✅ Dummy logo created at {logo_path}")
    print("✅ Test files generated.")
    return generated_paths