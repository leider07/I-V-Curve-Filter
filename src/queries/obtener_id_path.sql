SELECT {path_archivo}
FROM {tabla_curvas}
WHERE {analizador} = %s
AND DATE_FORMAT({datetime}, '%Y-%m-%d %H:%i') = %s
LIMIT 1