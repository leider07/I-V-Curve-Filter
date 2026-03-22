SELECT DISTINCT {analizador}
FROM {tabla_curvas}
ORDER BY CAST(SUBSTRING({analizador}, 4) AS UNSIGNED);