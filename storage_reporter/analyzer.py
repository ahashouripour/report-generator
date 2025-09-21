class DataAnalyzer:
    def __init__(self, con):
        self.con = con

    def analyze_source(self, source_path_or_paths):
        source_sql_str = f"[{', '.join([f'{p!r}' for p in source_path_or_paths])}]" if isinstance(source_path_or_paths, list) else f"{source_path_or_paths!r}"
        return self._perform_aggregations(source_sql_str)

    def _perform_aggregations(self, source_sql_str):
        cte = f"""
            WITH source_data AS (
                SELECT
                    project_id,
                    bucket_name,
                    TRY_CAST(size_bytes AS UBIGINT) as size_bytes,
                    COALESCE(NULLIF(TRIM(content_type), ''), 'unknown') as content_type,
                    TRY_CAST(creation_time_utc AS TIMESTAMP) as created_ts
                FROM read_csv_auto({source_sql_str}, ignore_errors=true, union_by_name=true)
            )
        """
        queries = {
            'summary': f"{cte} SELECT COUNT(*), SUM(size_bytes) FROM source_data",
            'top_projects': f"{cte} SELECT project_id, SUM(size_bytes) as total_size FROM source_data WHERE project_id IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10",
            'top_buckets': f"{cte} SELECT bucket_name, SUM(size_bytes) as total_size FROM source_data WHERE bucket_name IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10",
            'distribution_by_project': f"{cte} SELECT project_id, SUM(size_bytes) as total_size FROM source_data WHERE project_id IS NOT NULL GROUP BY 1 ORDER BY 2 DESC",
            'monthly_growth': f"{cte} SELECT date_trunc('month', created_ts) as month, SUM(size_bytes) as monthly_size FROM source_data WHERE created_ts IS NOT NULL GROUP BY 1 ORDER BY 1",
            'yearly_growth': f"{cte} SELECT date_trunc('year', created_ts) as year, SUM(size_bytes) as yearly_size FROM source_data WHERE created_ts IS NOT NULL GROUP BY 1 ORDER BY 1",

            'size_distribution': f"""{cte}
                SELECT CASE
                    WHEN size_bytes IS NULL OR size_bytes = 0 THEN '0 B'
                    WHEN size_bytes < 1024 THEN '< 1 KB'
                    WHEN size_bytes < 1024*1024 THEN '1 KB - 1 MB'
                    WHEN size_bytes < 1024*1024*1024 THEN '1 MB - 1 GB'
                    WHEN size_bytes < 1024*1024*1024*1024::BIGINT THEN '1 GB - 1 TB'
                    ELSE '> 1 TB'
                END as size_category, COUNT(*) as object_count
                FROM source_data GROUP BY 1
            """
        }
        results = {}
        for name, query in queries.items():
            results[name] = self.con.execute(query).fetchone() if name == 'summary' else self.con.execute(query).df()
        return results