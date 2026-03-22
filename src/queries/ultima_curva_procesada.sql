SELECT 
    {analizador},
    {datetime},
    CONCAT(
        {analizador}, '_',
        DATE_FORMAT({datetime}, '%y.%m.%d'), '_',
        DATE_FORMAT({datetime}, '%H.%i.%s'),
        '.parquet'
    ) AS ID_Curva
FROM 
    {tabla_resultados_ajuste}
ORDER BY 
    {datetime} DESC
LIMIT 1;