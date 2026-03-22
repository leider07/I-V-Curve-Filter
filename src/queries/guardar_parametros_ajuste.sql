INSERT INTO {tabla_resultados_ajuste} (
    {Coef_Pearson}, {Coef_Spearman}, {Iph_0}, {Is_0}, {nd_0}, {Rs_0}, {Rp_0}, 
    {Iph_f}, {Is_f}, {nd_f}, {Rs_f}, {Rp_f}, {analizador}, {fecha_hora}, {Metodo_usado}, {Error_metodo}
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
);