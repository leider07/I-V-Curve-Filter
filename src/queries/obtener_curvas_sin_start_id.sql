SELECT 
    {path_archivo},
    SUBSTRING_INDEX(SUBSTRING_INDEX({path_archivo}, '/', -1), '.parquet', 1) AS id_curva
FROM 
    {tabla_curvas}
WHERE 
    {analizador} = %s
ORDER BY 
    `{datetime}`,
    SUBSTRING_INDEX(SUBSTRING_INDEX({path_archivo}, '/', -1), '_', -1)