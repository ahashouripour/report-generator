import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import pandas as pd
from .utils import format_bytes

class ChartGenerator:
    def __init__(self, config, charts_dir):
        self.config = config
        self.charts_dir = charts_dir
        self.charts_dir.mkdir(exist_ok=True)
        plt.style.use(config['chart_style'])

    def generate_all_charts(self, aggs, prefix):
        chart_paths = {
            "Chart: Storage Dashboard": self._create_dashboard(aggs, prefix),
            "Chart: Top 10 Projects by Size": self._plot_barh(aggs['top_projects'], 'project_id', 'total_size', 'Top 10 Projects by Size', self.charts_dir / f"{prefix}_top_projects.png"),
            "Chart: Top 10 Buckets by Size": self._plot_barh(aggs['top_buckets'], 'bucket_name', 'total_size', 'Top 10 Buckets by Size', self.charts_dir / f"{prefix}_top_buckets.png"),
            "Chart: Storage Distribution by Project": self._plot_pie(aggs['distribution_by_project'], 'project_id', 'total_size', 'Storage Distribution by Project', self.charts_dir / f"{prefix}_distribution_by_project_pie.png"),
            "Chart: File Size Distribution": self._plot_bar(aggs['size_distribution'], 'size_category', 'object_count', 'File Size Distribution', self.charts_dir / f"{prefix}_size_distribution.png"),
            "Chart: Cumulative Monthly Storage Growth": self._plot_timeseries(aggs['monthly_growth'], 'month', 'monthly_size', 'Cumulative Monthly Storage Growth', self.charts_dir / f"{prefix}_monthly_growth.png", time_unit='month'),
            "Chart: Cumulative Yearly Storage Growth": self._plot_timeseries(aggs['yearly_growth'], 'year', 'yearly_size', 'Cumulative Yearly Storage Growth', self.charts_dir / f"{prefix}_yearly_growth.png", time_unit='year')
        }
        return {k: v for k, v in chart_paths.items() if v is not None}

    def _plot_barh(self, df, cat_col, val_col, title, save_path):
        if df.empty: 
            return None
        fig, ax = plt.subplots(figsize=(10, 7))
        df = df.sort_values(by=val_col, ascending=True)
        bars = ax.barh(df[cat_col], df[val_col], color='skyblue')
        ax.set_title(title, fontsize=self.config['chart_title_fontsize'])
        ax.set_xlabel('Total Size', fontsize=self.config['chart_label_fontsize'])
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_bytes(x)))
        ax.bar_label(bars, labels=[format_bytes(s) for s in df[val_col]], padding=3)
        ax.tick_params(axis='both', which='major', labelsize=self.config['chart_label_fontsize'])
        fig.tight_layout()
        plt.savefig(save_path, dpi=120)
        plt.close(fig)
        return save_path

    def _plot_pie(self, df, label_col, val_col, title, save_path):
        if df.empty: return None
        fig, ax = plt.subplots(figsize=(10, 8))
        
        if len(df) == 1:
            item_name = df[label_col].iloc[0]
            size = df[val_col].iloc[0]
            ax.bar([item_name], [size], color='steelblue', width=0.5)
            ax.set_title(title + "\n(Single Item Found)", fontsize=self.config['chart_title_fontsize'])
            ax.set_ylabel('Total Size', fontsize=self.config['chart_label_fontsize'])
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_bytes(x)))
            ax.text(0, size, f' {format_bytes(size)}', ha='center', va='bottom', fontsize=12, weight='bold')
            ax.tick_params(axis='both', which='major', labelsize=self.config['chart_label_fontsize'])
        else:
            df_copy = df.copy().sort_values(val_col, ascending=False)
            
            if len(df_copy) > 5: 
                top_5 = df_copy.head(5)
                others_size = df_copy.iloc[5:][val_col].sum()
                others_row = pd.DataFrame({label_col: ['Others'], val_col: [others_size]})
                grouped_df = pd.concat([top_5, others_row])
                
            else: 
                grouped_df = df_copy
            
            def autopct_format(pct): 
                return f'{pct:.1f}%' if pct > 3 else ''
            
            wedges, _, autotexts = ax.pie(grouped_df[val_col], autopct=autopct_format, startangle=90, pctdistance=0.85)
            plt.setp(autotexts, size=10, weight="bold", color="white")
            ax.legend(wedges, [f"{label} ({format_bytes(size)})" for label, size in zip(grouped_df[label_col], grouped_df[val_col])], title=label_col.replace('_', ' ').title(), loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            ax.set_title(title, fontsize=self.config['chart_title_fontsize'])
            ax.axis('equal')
        fig.tight_layout()
        plt.savefig(save_path, dpi=120)
        plt.close(fig)
        return save_path

    # --- UPDATED: Use dynamic rotation ---
    def _plot_bar(self, df, cat_col, val_col, title, save_path):
        if df.empty: 
            return None
        
        category_order = ['0 B', '< 1 KB', '1 KB - 1 MB', '1 MB - 1 GB', '1 GB - 1 TB', '> 1 TB']
        df[cat_col] = pd.Categorical(df[cat_col], categories=category_order, ordered=True)
        df = df.sort_values(cat_col)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(df[cat_col], df[val_col], color='purple')
        ax.set_title(title, fontsize=self.config['chart_title_fontsize'])
        ax.set_ylabel('Number of Objects (Log Scale)', fontsize=self.config['chart_label_fontsize'])
        ax.set_yscale('log')

        rotation = self.config['chart_xaxis_rotation']
        ha = "right" if rotation > 0 else "center"
        plt.xticks(rotation=rotation, ha=ha)

        ax.tick_params(axis='both', which='major', labelsize=self.config['chart_label_fontsize'])
        fig.tight_layout()
        plt.savefig(save_path, dpi=120)
        plt.close(fig)
        
        return save_path

    # --- UPDATED: Use dynamic rotation ---
    def _plot_timeseries(self, df, date_col, val_col, title, save_path, time_unit='month'):
        if df.empty or df[date_col].isnull().all(): 
            return None

        df_copy = df.copy().sort_values(by=date_col)
        df_copy['cumulative_size'] = df_copy[val_col].cumsum()

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_copy[date_col], df_copy['cumulative_size'], marker='.', linestyle='-')
        ax.fill_between(df_copy[date_col], df_copy['cumulative_size'], alpha=0.2)

        ax.set_title(title, fontsize=self.config['chart_title_fontsize'])
        ax.set_ylabel('Total Storage', fontsize=self.config['chart_label_fontsize'])
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_bytes(x)))
        ax.tick_params(axis='both', which='major', labelsize=self.config['chart_label_fontsize'])

        if time_unit == 'year':
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        else:
            num_months = len(df_copy[date_col].unique())
            interval = 6 if num_months > 24 else 3 if num_months > 12 else 1
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        rotation = self.config['chart_xaxis_rotation']
        ha = "right" if rotation > 0 else "center"
        plt.setp(ax.get_xticklabels(), rotation=rotation, ha=ha)

        fig.tight_layout()
        plt.savefig(save_path, dpi=120)
        plt.close(fig)
        return save_path

    def _create_dashboard(self, aggs, prefix):
        save_path = self.charts_dir / f"{prefix}_dashboard.png"
        fig = plt.figure(figsize=(20, 14), constrained_layout=True)
        fig.suptitle('Storage Analysis Dashboard', fontsize=28, weight='bold')
        gs = fig.add_gridspec(2, 2)
        ax_main = fig.add_subplot(gs[0, 0])
        ax_main.axis('off')
        total_objects, total_size = aggs['summary']
        text = (f"Total Objects\n{total_objects:,}\n\nTotal Storage\n{format_bytes(total_size)}")
        ax_main.text(0.5, 0.5, text, ha='center', va='center', fontsize=24, bbox=dict(boxstyle="round,pad=0.5", fc="aliceblue", ec="b", lw=2))
        ax_pie = fig.add_subplot(gs[0, 1])
        df_proj = aggs['distribution_by_project']
        pie_chart_path_for_dashboard = self.charts_dir / f"{prefix}_dashboard_pie_temp.png"
        self._plot_pie(df_proj, 'project_id', 'total_size', 'Storage by Project', pie_chart_path_for_dashboard)
        
        if pie_chart_path_for_dashboard.exists(): 
            ax_pie.imshow(plt.imread(pie_chart_path_for_dashboard))
        
        pie_chart_path_for_dashboard.unlink()
        ax_pie.axis('off')
        ax_buckets = fig.add_subplot(gs[1, 0])
        df_buckets = aggs['top_buckets']
        
        if not df_buckets.empty:
            df_buckets = df_buckets.sort_values('total_size', ascending=True)
        
        bars = ax_buckets.barh(df_buckets['bucket_name'], df_buckets['total_size'], color='teal')
        ax_buckets.set_title('Top Buckets by Size', fontsize=18)
        ax_buckets.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_bytes(x)))
        ax_buckets.bar_label(bars, labels=[format_bytes(s) for s in df_buckets['total_size']], padding=3, fontsize=10)
        ax_buckets.tick_params(axis='both', which='major', labelsize=12)
        ax_dist = fig.add_subplot(gs[1, 1])
        df_dist = aggs['size_distribution']
        
        if not df_dist.empty:
            category_order = ['0 B', '< 1 KB', '1 KB - 1 MB', '1 MB - 1 GB', '1 GB - 1 TB', '> 1 TB']
            df_dist['size_category'] = pd.Categorical(df_dist['size_category'], categories=category_order, ordered=True)
            df_dist = df_dist.sort_values('size_category').dropna()
            ax_dist.bar(df_dist['size_category'], df_dist['object_count'], color='indigo')
            ax_dist.set_yscale('log')
            ax_dist.set_title('Size Distribution', fontsize=18)
            ax_dist.tick_params(axis='x', rotation=45, labelsize=12)
            ax_dist.tick_params(axis='y', which='major', labelsize=12)
            
        plt.savefig(save_path, dpi=150)
        plt.close(fig)
        return save_path
    