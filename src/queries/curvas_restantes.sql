SELECT 
    {path_archivo},
    SUBSTRING_INDEX(SUBSTRING_INDEX({path_archivo}, '/', -1), '.parquet', 1) AS id_curva
FROM 
    {tabla_curvas}
WHERE 
    {analizador} = %s  
    AND `{datetime}` > %s 
ORDER BY 
    `{datetime}` ASC
LIMIT 1