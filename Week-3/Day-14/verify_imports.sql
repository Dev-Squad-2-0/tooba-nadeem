SELECT
    table_schema,
    table_name,
    (
        xpath('/row/cnt/text()',
            query_to_xml(
                format('SELECT COUNT(*) AS cnt FROM %I.%I',
                table_schema,
                table_name),
                false,
                true,
                ''
            )
        )
    )[1]::text::int AS row_count
FROM information_schema.tables
WHERE table_schema IN (
    'sales',
    'production',
    'purchasing',
    'humanresources',
    'person'
)
AND table_type = 'BASE TABLE'
ORDER BY table_schema, table_name;