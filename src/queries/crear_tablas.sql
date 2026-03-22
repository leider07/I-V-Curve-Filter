-- -----------------------------------------------------
-- Crea la tabla '{table_parameters_metodologia1}'
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS {table_parameters_metodologia1} (
  ID INT(11) NOT NULL AUTO_INCREMENT,                 -- Identificador único del parámetro
  Datetime DATETIME NOT NULL,                         -- Fecha y hora del parámetro
  Voc FLOAT NULL,                                     -- Tensión en circuito abierto
  Voce FLOAT NULL,                                    -- Error en la tensión en circuito abierto
  FF FLOAT NULL,                                      -- Factor de forma
  Isc FLOAT NULL,                                     -- Corriente de cortocircuito
  Pmax FLOAT NULL,                                    -- Potencia máxima
  Vmpp FLOAT NULL,                                    -- Tensión en el punto de máxima potencia
  Impp FLOAT NULL,                                    -- Corriente en el punto de máxima potencia
  Vmin FLOAT NULL,                                    -- Tensión mínima
  Imin FLOAT NULL,                                    -- Corriente mínima
  Analizador VARCHAR(40) NOT NULL,                    -- Identificador de la curva asociada
  PRIMARY KEY (ID, Analizador),                       -- Clave primaria combinada en 'ID' y 'Analizador'
  CONSTRAINT fk_Parameters_Grupo_Solar_Curvas1        -- Define la clave foránea hacia la tabla '{table_curvas}'
    FOREIGN KEY (Analizador)
    REFERENCES {table_curvas} (Analizador)
    ON DELETE NO ACTION                                 -- Acciones a realizar en caso de eliminación (sin acción)
    ON UPDATE NO ACTION                                 -- Acciones a realizar en caso de actualización (sin acción)
) ENGINE = InnoDB;                                      -- Define el motor de almacenamiento como InnoDB

-- -----------------------------------------------------
-- Crea la tabla '{table_parameters_metodologia2}'
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS {table_parameters_metodologia2} (
  ID INT(11) NOT NULL AUTO_INCREMENT,                 -- Identificador único del parámetro
  Datetime DATETIME NOT NULL,                         -- Fecha y hora del parámetro
  Voc FLOAT NULL,                                     -- Tensión en circuito abierto
  Voce FLOAT NULL,                                    -- Error en la tensión en circuito abierto
  FF FLOAT NULL,                                      -- Factor de forma
  Isc FLOAT NULL,                                     -- Corriente de cortocircuito
  Pmax FLOAT NULL,                                    -- Potencia máxima
  Vmpp FLOAT NULL,                                    -- Tensión en el punto de máxima potencia
  Impp FLOAT NULL,                                    -- Corriente en el punto de máxima potencia
  Vmin FLOAT NULL,                                    -- Tensión mínima
  Imin FLOAT NULL,                                    -- Corriente mínima
  Analizador VARCHAR(40) NOT NULL,                    -- Identificador de la curva asociada
  PRIMARY KEY (ID, Analizador),                       -- Clave primaria combinada en 'ID' y 'Analizador'
  CONSTRAINT fk_Parameters_Grupo_Solar_Curvas2        -- Define la clave foránea hacia la tabla '{table_curvas}'
    FOREIGN KEY (Analizador)
    REFERENCES {table_curvas} (Analizador)
    ON DELETE NO ACTION                               -- Acciones a realizar en caso de eliminación (sin acción)
    ON UPDATE NO ACTION                               -- Acciones a realizar en caso de actualización (sin acción)
) ENGINE = InnoDB;                                    -- Define el motor de almacenamiento como InnoDB

-- -----------------------------------------------------
-- Crea la tabla '{table_resultados_ajuste}'
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS {table_resultados_ajuste} (
  ID INT(11) NOT NULL AUTO_INCREMENT,                 -- Identificador único del resultado de ajuste
  coef_pearson FLOAT NULL,                            -- Coeficiente de Pearson
  coef_spearman FLOAT NULL,                           -- Coeficiente de Spearman
  iph_0 FLOAT NULL,                                   -- Valor inicial de iph
  is_0 DOUBLE NULL,                                   -- Valor inicial de is
  nd_0 FLOAT NULL,                                    -- Valor inicial de nd
  rs_0 FLOAT NULL,                                    -- Valor inicial de rs
  rp_0 FLOAT NULL,                                    -- Valor inicial de rp
  iph_f FLOAT NULL,                                   -- Valor final de iph
  is_f DOUBLE NULL,                                   -- Valor final de is
  nd_f FLOAT NULL,                                    -- Valor final de nd
  rs_f FLOAT NULL,                                    -- Valor final de rs
  rp_f FLOAT NULL,                                    -- Valor final de rp
  Analizador VARCHAR(40) NOT NULL,                    -- Identificador de la curva asociada
  Datetime DATETIME NOT NULL,
  metodo_usado VARCHAR(15),                           -- Metodo usado en el ajuste
  error_metodo FLOAT NULL,                            -- Error del metodo usado
  PRIMARY KEY (ID),                                   -- Clave primaria en 'id'
  CONSTRAINT fk_resultados_ajuste_Curvas              -- Define la clave foránea hacia la tabla '{table_curvas}'
    FOREIGN KEY (Analizador)
    REFERENCES {table_curvas} (Analizador)
    ON DELETE NO ACTION                                 -- Acciones a realizar en caso de eliminación (sin acción)
    ON UPDATE NO ACTION                                 -- Acciones a realizar en caso de actualización (sin acción)
) ENGINE = InnoDB;                                      -- Define el motor de almacenamiento como InnoDB