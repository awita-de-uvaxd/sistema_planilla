import os
import sqlite3
from werkzeug.security import generate_password_hash
 
def get_db_path():
    # Construye la ruta absoluta basada en la ubicación del archivo
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.abspath(os.path.join(base_dir, '..', 'instance'))
    os.makedirs(instance_path, exist_ok=True)
    return os.path.join(instance_path, 'sistema_planillas.db')
 
def get_db_connection():
    # Función centralizada que activa Foreign Keys en SQLite
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn
 
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
 
    # 1. TABLA: DEPARTAMENTOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departamento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT UNIQUE NOT NULL
    );
    """)
 
    # 2. TABLA: USUARIOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        pass_admin_auth TEXT DEFAULT 'admin123',
        rol TEXT NOT NULL CHECK(rol IN ('ADMIN', 'RRHH', 'OPERADOR')),
        correo TEXT,
        telefono TEXT,
        permisos TEXT DEFAULT 'ALL',
        activo INTEGER DEFAULT 1
    );
    """)
 
    # 3. TABLA: EMPLEADOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS empleado (
        dpi TEXT PRIMARY KEY,
        fecha_ingreso TEXT NOT NULL,
        nombre TEXT NOT NULL,
        direccion TEXT,
        telefono TEXT,
        celular TEXT,
        nit TEXT,
        senales TEXT DEFAULT 'NINGUNA',
        enfermedad TEXT DEFAULT 'NINGUNA',
        empresa TEXT DEFAULT 'TECNIMARKET S.A. DE GUATEMALA',
        departamento_id INTEGER,
        cargo TEXT NOT NULL,
        tipo_origen TEXT NOT NULL CHECK(tipo_origen IN ('LOCAL', 'EXTRANJERO')),
        pais TEXT DEFAULT 'Guatemala',
        visa TEXT,
        moneda TEXT NOT NULL CHECK(moneda IN ('GTQ', 'USD')),
        sueldo_base REAL NOT NULL,
        tipo_pago TEXT DEFAULT 'Mensual',
        aplica_igss INTEGER DEFAULT 1,
        aplica_bono INTEGER DEFAULT 1,
        aplica_isr INTEGER DEFAULT 1,
        estado_civil TEXT,
        hijos INTEGER DEFAULT 0,
        conyuge TEXT,
        tel_conyuge TEXT,
        foto TEXT,
        estado TEXT DEFAULT 'ACTIVO' CHECK(estado IN ('ACTIVO', 'INACTIVO')),
        FOREIGN KEY (departamento_id) REFERENCES departamento(id) ON DELETE SET NULL
    );
    """)
 
    # 4. TABLA: ASISTENCIA DIARIA
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empleado_dpi TEXT NOT NULL,
        fecha TEXT NOT NULL,
        hora_entrada TEXT DEFAULT '08:00 AM',
        novedad TEXT DEFAULT 'NORMAL' CHECK(novedad IN ('NORMAL', 'IGSS', 'PERMISO', 'VACACIONES')),
        entrada_diferencial REAL DEFAULT 0.0,
        hora_salida TEXT DEFAULT '05:00 PM',
        horas_extra REAL DEFAULT 0.0,
        tarifa_extra REAL DEFAULT 20.0,
        aplica_pago INTEGER DEFAULT 1,
        total_extra REAL DEFAULT 0.0,
        FOREIGN KEY (empleado_dpi) REFERENCES empleado(dpi) ON DELETE CASCADE
    );
    """)
 
    # 5. TABLA: BAJAS Y FINIQUITOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS baja_finiquito (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empleado_dpi TEXT NOT NULL,
        tipo_baja TEXT NOT NULL CHECK(tipo_baja IN ('DESPIDO', 'RENUNCIA')),
        fecha_baja TEXT NOT NULL,
        dias_mes_laborados INTEGER NOT NULL,
        dias_vacaciones_pendientes REAL NOT NULL,
        observaciones TEXT,
        salario_pendiente REAL NOT NULL,
        bono_incentivo_prop REAL NOT NULL,
        aguinaldo_prop REAL NOT NULL,
        bono14_prop REAL NOT NULL,
        vacaciones_prop REAL NOT NULL,
        indemnizacion REAL DEFAULT 0.0,
        total_liquidado REAL NOT NULL,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (empleado_dpi) REFERENCES empleado(dpi) ON DELETE CASCADE
    );
    """)
 
    # 6. TABLA: EX_EMPLEADOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ex_empleado (
        dpi TEXT PRIMARY KEY,
        codigo TEXT,
        nombre TEXT NOT NULL,
        departamento TEXT,
        cargo TEXT,
        causal_salida TEXT NOT NULL,
        fecha_salida TEXT NOT NULL,
        monto_liquidado REAL NOT NULL,
        foto TEXT,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
 
    # Índices para consultas por DPI
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_empleado_dpi ON empleado(dpi);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ex_empleado_dpi ON ex_empleado(dpi);")
 
    # DATOS INICIALES (SEEDING)
    deptos = [
        ('DEP-01', 'DESARROLLO'),
        ('DEP-02', 'DISEÑO'),
        ('DEP-03', 'VENTAS'),
        ('DEP-04', 'ATENCION AL CLIENTE'),
        ('DEP-05', 'ADMINISTRACION'),
        ('DEP-06', 'MERCADEO'),
        ('DEP-07', 'CONTABILIDAD')
    ]
    cursor.executemany("INSERT OR IGNORE INTO departamento (codigo, nombre) VALUES (?, ?);", deptos)
 
    usuarios = [
        ('admin', generate_password_hash('admin123'), generate_password_hash('admin123'), 'ADMIN', 'admin@tecnimarket.gt', '2222-3333', 'ALL', 1),
        ('rrhh', generate_password_hash('rrhh123'), '', 'RRHH', 'rrhh@tecnimarket.gt', '5555-4444', 'dashboard,empleados,locales,extranjeros,directorio,planillas,asistencia,bajas,ex-empleados', 1),
        ('operador', generate_password_hash('op123'), '', 'OPERADOR', 'operador@tecnimarket.gt', '4444-1111', 'dashboard,asistencia', 1)
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO usuario (username, password, pass_admin_auth, rol, correo, telefono, permisos, activo) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, usuarios)
 
    empleados = [
        (
            '2024-01-15', 'JOSE FLORES GUZMÁN', 'ZONA 10, CIUDAD DE GUATEMALA',
            '2222-2222', '5555-5555', '2540123450101', '1010123-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'CONTADOR GENERAL', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4500.00, 'Mensual', 1, 1, 1, 'Casado', 2, 'CELINA FLORES', '2525-3030',
            'https://placehold.co/150x180/3b82f6/ffffff?text=JOSE+FLORES', 'ACTIVO'
        ),
        (
            '2024-03-01', 'MARIO RIVAS', 'ZONA 11, MIXCO, GUATEMALA',
            '2333-4444', '4444-1111', '1890987650101', '882312-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'EJECUTIVO DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 3800.00, 'Mensual', 1, 1, 0, 'Soltero', 0, '', '',
            'https://placehold.co/150x180/10b981/ffffff?text=MARIO+RIVAS', 'ACTIVO'
        ),
        (
            '2023-11-10', 'SONIA FIGUEROA', 'CARRETERA A EL SALVADOR, KM 14',
            '2444-5555', '3333-2222', '3001456780101', '991204-1', 'NINGUNA', 'INCAPACIDAD PARCIAL',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'INGENIERA DE SOFTWARE EXPATRIADA', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1200.00, 'Mensual', 1, 1, 1, 'Casado', 1, 'CARLOS FIGUEROA', '2444-9999',
            'https://placehold.co/150x180/8b5cf6/ffffff?text=SONIA+F', 'ACTIVO'
        )
    ]
    empleados.extend([
        (
            '2023-12-25', 'LETICIA ESTRADA CHÁVEZ', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2425-4931', '3728-2322', '3279651300501', '1957850-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'CONTADOR', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6400.00, 'Mensual', 1, 1, 1, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2024-09-21', 'MARVIN REYES MENDOZA', 'VILLA NUEVA, GUATEMALA',
            '2374-2469', '5650-5786', '2424567450901', '4925159-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'DISEÑADOR UX/UI', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7100.00, 'Mensual', 1, 1, 1, 'Casado', 2, 'MARÍA REYES', '4472-8554',
            '', 'ACTIVO'
        ),
        (
            '2022-09-09', 'SANDRA ESCOBAR CONTRERAS', 'SAN MIGUEL PETAPA, GUATEMALA',
            '2488-8851', '5630-1415', '3074886640901', '9755560-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'CONTADOR', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7700.00, 'Mensual', 1, 1, 1, 'Casada', 0, 'BYRON ESCOBAR', '2834-8035',
            '', 'ACTIVO'
        ),
        (
            '2025-05-01', 'GLORIA SANDOVAL TORRES', 'SANTA CATARINA PINULA, GUATEMALA',
            '2276-8507', '5601-6897', 'G48876634', '3452718-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'ADMINISTRADOR DE BASE DE DATOS', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2400.00, 'Mensual', 1, 1, 1, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2022-12-23', 'MARVIN LEMUS CRUZ', 'ZONA 7, CIUDAD DE GUATEMALA',
            '2431-3999', '4962-8850', '2297699850101', '1178693-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'ASISTENTE ADMINISTRATIVO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4400.00, 'Mensual', 1, 1, 0, 'Casado', 3, 'WENDY LEMUS', '2299-7738',
            '', 'ACTIVO'
        ),
        (
            '2019-09-09', 'MARÍA MARTÍNEZ GARCÍA', 'ZONA 18, CIUDAD DE GUATEMALA',
            '2279-1084', '4780-9060', '2015258350501', '2362652-8', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 3800.00, 'Mensual', 1, 1, 0, 'Casada', 3, 'KEVIN MARTÍNEZ', '3712-9269',
            '', 'ACTIVO'
        ),
        (
            '2019-06-21', 'ROSA ROMERO GONZÁLEZ', 'ZONA 7, CIUDAD DE GUATEMALA',
            '2213-1419', '5587-6370', 'G28360161', '5194766-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'ANALISTA FINANCIERO', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2500.00, 'Mensual', 1, 1, 1, 'Casada', 0, 'MARVIN ROMERO', '5685-3797',
            '', 'ACTIVO'
        ),
        (
            '2019-09-13', 'ANDRÉS CRUZ SOLÍS', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2300-3840', '3763-9925', '1955989320301', '908451-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'SUPERVISOR DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7900.00, 'Mensual', 1, 1, 1, 'Casado', 3, 'MARÍA CRUZ', '3761-9682',
            '', 'ACTIVO'
        ),
        (
            '2023-07-28', 'BYRON TORRES GONZÁLEZ', 'ZONA 18, CIUDAD DE GUATEMALA',
            '2396-5995', '3452-3862', '2597457570901', '4519851-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'ILUSTRADOR DIGITAL', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4550.00, 'Mensual', 1, 1, 0, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2021-03-12', 'BRENDA ESTRADA CONTRERAS', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2256-5595', '5869-4513', 'D01756820', '9660245-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1200.00, 'Mensual', 1, 1, 1, 'Unida', 2, 'ERICK ESTRADA', '3203-5320',
            '', 'ACTIVO'
        ),
        (
            '2019-09-11', 'PEDRO PÉREZ REYES', 'ZONA 18, CIUDAD DE GUATEMALA',
            '2232-5768', '4265-5273', '1759946650301', '4397049-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'ANALISTA QA', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7300.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2023-10-28', 'MARÍA LÓPEZ PÉREZ', 'ANTIGUA GUATEMALA, SACATEPÉQUEZ',
            '2361-8471', '5740-1622', '1503223030301', '6881192-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'DISEÑADOR GRÁFICO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 5450.00, 'Mensual', 1, 1, 1, 'Unida', 1, 'WILLIAM LÓPEZ', '5536-2956',
            '', 'ACTIVO'
        ),
        (
            '2024-07-01', 'LETICIA REYES ROMERO', 'CHINAUTLA, GUATEMALA',
            '2369-5744', '5887-3004', '2459175530301', '5081860-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'SUPERVISOR DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6900.00, 'Mensual', 1, 1, 1, 'Casada', 0, 'ERICK REYES', '4302-1919',
            '', 'ACTIVO'
        ),
        (
            '2020-07-22', 'PEDRO SOLÍS PÉREZ', 'SANTA CATARINA PINULA, GUATEMALA',
            '2264-4005', '5129-9869', 'E06925666', '9409646-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR BACKEND', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2550.00, 'Mensual', 1, 1, 1, 'Casado', 1, 'GLORIA SOLÍS', '2116-5535',
            '', 'ACTIVO'
        ),
        (
            '2024-09-27', 'KARLA MENDOZA GONZÁLEZ', 'ZONA 7, CIUDAD DE GUATEMALA',
            '2374-9527', '5425-1921', '1734824800101', '291416-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'COORDINADOR DE MARCA', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6550.00, 'Mensual', 1, 1, 1, 'Casada', 3, 'CARLOS MENDOZA', '3795-9333',
            '', 'ACTIVO'
        ),
        (
            '2021-08-21', 'ROBERTO AGUILAR ORTIZ', 'SAN MIGUEL PETAPA, GUATEMALA',
            '2480-8767', '5694-6114', '2407363420103', '3252477-2', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'CONTADOR', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6750.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2020-12-19', 'EDUARDO MÉNDEZ MÉNDEZ', 'MIXCO, GUATEMALA',
            '2493-1731', '4489-9830', 'B45842108', '8767041-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'ENCARGADO DE RECURSOS HUMANOS', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1000.00, 'Mensual', 1, 1, 1, 'Casado', 0, 'SOFÍA MÉNDEZ', '3850-7376',
            '', 'ACTIVO'
        ),
        (
            '2021-06-05', 'RICARDO LÓPEZ BARRIOS', 'SANTA CATARINA PINULA, GUATEMALA',
            '2296-1154', '5763-8864', '2199487040501', '7190939-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'GERENTE ADMINISTRATIVO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 10000.00, 'Mensual', 1, 1, 1, 'Unido', 1, 'LETICIA LÓPEZ', '2283-6155',
            '', 'ACTIVO'
        ),
        (
            '2020-09-05', 'MARÍA TORRES PÉREZ', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2264-2741', '4596-2759', '1260582340103', '1326936-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'ASISTENTE ADMINISTRATIVO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4650.00, 'Mensual', 1, 1, 0, 'Casada', 2, 'JOSÉ TORRES', '4585-9171',
            '', 'ACTIVO'
        ),
        (
            '2023-09-11', 'DIEGO MÉNDEZ ORTIZ', 'SAN MIGUEL PETAPA, GUATEMALA',
            '2452-7603', '4280-4219', 'B17443256', '7867968-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'ANALISTA DE MERCADEO', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2000.00, 'Mensual', 1, 1, 1, 'Casado', 2, 'MÓNICA MÉNDEZ', '5317-3529',
            '', 'ACTIVO'
        ),
        (
            '2020-09-21', 'MIGUEL CRUZ MORALES', 'ANTIGUA GUATEMALA, SACATEPÉQUEZ',
            '2319-6435', '3674-3019', '2091682540103', '4594784-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'EJECUTIVO DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4800.00, 'Mensual', 1, 1, 0, 'Unido', 3, 'ILSY CRUZ', '5122-6393',
            '', 'ACTIVO'
        ),
        (
            '2019-07-24', 'LUCÍA REYES CIFUENTES', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2205-5375', '5818-5131', '2442949640103', '2291090-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4550.00, 'Mensual', 1, 1, 0, 'Unida', 3, 'MARVIN REYES', '5446-1192',
            '', 'ACTIVO'
        ),
        (
            '2021-10-21', 'JOSÉ REYES SANDOVAL', 'CHINAUTLA, GUATEMALA',
            '2240-4074', '5887-1186', '1856699170501', '1703776-2', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'SUPERVISOR DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6050.00, 'Mensual', 1, 1, 1, 'Casado', 1, 'CLAUDIA REYES', '3720-3798',
            '', 'ACTIVO'
        ),
        (
            '2021-06-20', 'SANDRA CRUZ AGUILAR', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2330-9000', '4959-5097', 'G02883755', '715983-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'GERENTE ADMINISTRATIVO', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 950.00, 'Mensual', 1, 1, 1, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2025-12-13', 'WENDY MORALES MÉNDEZ', 'SANTA CATARINA PINULA, GUATEMALA',
            '2311-1887', '4983-2057', '2505458650501', '8638950-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'AUXILIAR CONTABLE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 3800.00, 'Mensual', 1, 1, 0, 'Unida', 2, 'MARVIN MORALES', '2973-9349',
            '', 'ACTIVO'
        ),
        (
            '2025-05-28', 'MARVIN MENDOZA REYES', 'CHINAUTLA, GUATEMALA',
            '2254-4519', '3574-4946', '1319836680102', '3617681-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'SUPERVISOR DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6550.00, 'Mensual', 1, 1, 1, 'Unido', 1, 'LETICIA MENDOZA', '3910-5434',
            '', 'ACTIVO'
        ),
        (
            '2021-05-27', 'DIANA REYES MÉNDEZ', 'VILLA NUEVA, GUATEMALA',
            '2271-5383', '5809-6843', 'C98222900', '2247305-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'AUXILIAR CONTABLE', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2150.00, 'Mensual', 1, 1, 1, 'Casada', 1, 'CARLOS REYES', '3796-3521',
            '', 'ACTIVO'
        ),
        (
            '2019-08-22', 'MARVIN ROMERO ESCOBAR', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2279-6316', '3831-9326', '3107577300501', '775668-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'ANALISTA QA', 'LOCAL', 'Guatemala',
            '', 'GTQ', 5700.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2024-07-07', 'KARLA MENDOZA CIFUENTES', 'CHINAUTLA, GUATEMALA',
            '2323-4680', '5606-4485', '1783218030901', '6346991-2', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 9200.00, 'Mensual', 1, 1, 1, 'Unida', 3, 'OSCAR MENDOZA', '5976-6950',
            '', 'ACTIVO'
        ),
        (
            '2020-07-01', 'ANDREA CHÁVEZ BARRIOS', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2337-5704', '5473-7525', 'B15921236', '259745-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'SUPERVISOR DE CALL CENTER', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1550.00, 'Mensual', 1, 1, 1, 'Unida', 3, 'FERNANDO CHÁVEZ', '4599-3260',
            '', 'ACTIVO'
        ),
        (
            '2021-05-22', 'ERICK RAMÍREZ ORTIZ', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2436-8676', '4659-9608', '1197978210501', '8997146-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'SUPERVISOR DE CALL CENTER', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6900.00, 'Mensual', 1, 1, 1, 'Casado', 2, 'ANA RAMÍREZ', '2704-1686',
            '', 'ACTIVO'
        ),
        (
            '2020-06-05', 'HÉCTOR PAZ PÉREZ', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2253-7419', '3272-9761', '2960808810101', '4377321-0', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'SUPERVISOR DE CALL CENTER', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6950.00, 'Mensual', 1, 1, 1, 'Soltero', 1, '', '',
            '', 'ACTIVO'
        ),
        (
            '2020-06-23', 'BYRON PÉREZ BARRIOS', 'CARRETERA A EL SALVADOR, KM 16',
            '2324-7554', '3626-6121', '1627502430901', '7127424-0', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'AUXILIAR CONTABLE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4600.00, 'Mensual', 1, 1, 0, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2020-09-11', 'PATRICIA CIFUENTES PÉREZ', 'MIXCO, GUATEMALA',
            '2421-1430', '4716-9519', 'A73608724', '2891061-8', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'ENCARGADO DE RECURSOS HUMANOS', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2100.00, 'Mensual', 1, 1, 1, 'Soltera', 1, '', '',
            '', 'ACTIVO'
        ),
        (
            '2022-01-08', 'KEVIN MARTÍNEZ ESCOBAR', 'SAN MIGUEL PETAPA, GUATEMALA',
            '2226-5303', '3637-5364', '1454238480901', '6378681-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'DISEÑADOR UX/UI', 'LOCAL', 'Guatemala',
            '', 'GTQ', 8050.00, 'Mensual', 1, 1, 1, 'Casado', 1, 'ANA MARTÍNEZ', '3823-2895',
            '', 'ACTIVO'
        ),
        (
            '2025-04-21', 'CARLOS ORTIZ TORRES', 'CARRETERA A EL SALVADOR, KM 16',
            '2224-5772', '3272-2073', '3111926380101', '4782900-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'ANALISTA DE MERCADEO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7150.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2020-01-01', 'MARVIN ROMERO MORALES', 'ANTIGUA GUATEMALA, SACATEPÉQUEZ',
            '2397-2464', '4791-3924', 'H08538671', '2978513-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2550.00, 'Mensual', 1, 1, 1, 'Casado', 1, 'LETICIA ROMERO', '4509-5569',
            '', 'ACTIVO'
        ),
        (
            '2025-04-27', 'HÉCTOR MARTÍNEZ GARCÍA', 'CHINAUTLA, GUATEMALA',
            '2276-6282', '3606-2890', '1533843030501', '2426783-0', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'EJECUTIVO DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6150.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2019-11-09', 'MÓNICA REYES PAZ', 'MIXCO, GUATEMALA',
            '2259-7180', '3411-3943', '1340993450501', '5248543-8', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'ASESOR COMERCIAL', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4600.00, 'Mensual', 1, 1, 0, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2022-05-01', 'PEDRO AGUILAR ALVARADO', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2351-3466', '4748-1082', 'H11209842', '7550406-9', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'ASISTENTE ADMINISTRATIVO', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2400.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2024-05-09', 'HÉCTOR LEMUS MARTÍNEZ', 'CHINAUTLA, GUATEMALA',
            '2410-8692', '4980-6130', '2121675110901', '2921124-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'AUXILIAR CONTABLE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 5000.00, 'Mensual', 1, 1, 1, 'Unido', 0, 'PATRICIA LEMUS', '3815-5824',
            '', 'ACTIVO'
        ),
        (
            '2022-03-20', 'ROBERTO RAMÍREZ SANDOVAL', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2474-7465', '3731-9996', '1679233040102', '5181476-8', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'COORDINADOR DE MARCA', 'LOCAL', 'Guatemala',
            '', 'GTQ', 8050.00, 'Mensual', 1, 1, 1, 'Unido', 3, 'KARLA RAMÍREZ', '4986-8408',
            '', 'ACTIVO'
        ),
        (
            '2023-03-15', 'ANDREA LÓPEZ BARRIOS', 'SANTA CATARINA PINULA, GUATEMALA',
            '2454-1969', '5414-1592', '1695664270301', '8720781-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'GERENTE ADMINISTRATIVO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 10900.00, 'Mensual', 1, 1, 1, 'Unida', 2, 'OSCAR LÓPEZ', '3807-9763',
            '', 'ACTIVO'
        ),
        (
            '2023-07-12', 'VERÓNICA ESTRADA ORTIZ', 'SANTA CATARINA PINULA, GUATEMALA',
            '2254-4868', '3279-9036', 'A68669538', '6703470-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'AUXILIAR CONTABLE', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2100.00, 'Mensual', 1, 1, 1, 'Casada', 3, 'BYRON ESTRADA', '3482-1509',
            '', 'ACTIVO'
        ),
        (
            '2024-02-14', 'LUCÍA PÉREZ HERNÁNDEZ', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2364-6088', '3199-2086', '2421933510501', '5833687-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4650.00, 'Mensual', 1, 1, 0, 'Casada', 3, 'OSCAR PÉREZ', '2759-2728',
            '', 'ACTIVO'
        ),
        (
            '2020-03-15', 'ERICK SANDOVAL CONTRERAS', 'SAN MIGUEL PETAPA, GUATEMALA',
            '2250-7940', '3193-1337', '1510213500103', '7880785-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'ASESOR COMERCIAL', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4050.00, 'Mensual', 1, 1, 0, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2019-03-20', 'SILVIA ORTIZ BARRIOS', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2332-8121', '3811-4709', 'B48836152', '6221919-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR BACKEND', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1450.00, 'Mensual', 1, 1, 1, 'Soltera', 1, '', '',
            '', 'ACTIVO'
        ),
        (
            '2022-05-02', 'WILLIAM MORALES MENDOZA', 'MIXCO, GUATEMALA',
            '2469-8538', '4523-5269', '3145337600501', '3588513-9', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'SUPERVISOR DE CALL CENTER', 'LOCAL', 'Guatemala',
            '', 'GTQ', 5700.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2021-12-11', 'RICARDO MORALES CASTILLO', 'VILLA NUEVA, GUATEMALA',
            '2372-7651', '5534-8565', '1811887570501', '6413879-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6000.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2023-01-28', 'HÉCTOR PAZ MENDOZA', 'CHINAUTLA, GUATEMALA',
            '2476-9924', '3218-6420', 'G54705670', '7343654-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'ENCARGADO DE RECURSOS HUMANOS', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 900.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2023-08-04', 'PATRICIA HERNÁNDEZ LÓPEZ', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2348-3079', '3995-7854', '1203581190501', '3948389-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7100.00, 'Mensual', 1, 1, 1, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2024-08-07', 'ROBERTO LÓPEZ GONZÁLEZ', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2412-6105', '3373-9784', '2675586280501', '2868058-9', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4100.00, 'Mensual', 1, 1, 0, 'Soltero', 1, '', '',
            '', 'ACTIVO'
        ),
        (
            '2025-02-26', 'SANDRA CRUZ MÉNDEZ', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2420-4140', '4858-8569', '1601101090103', '8888970-9', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'SUPERVISOR DE CALL CENTER', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7000.00, 'Mensual', 1, 1, 1, 'Casada', 1, 'ALEJANDRO CRUZ', '3881-5835',
            '', 'ACTIVO'
        ),
        (
            '2019-05-18', 'ANDRÉS ALVARADO VÁSQUEZ', 'ANTIGUA GUATEMALA, SACATEPÉQUEZ',
            '2478-2198', '5330-8601', 'F91483354', '9465620-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'ANALISTA QA', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1100.00, 'Mensual', 1, 1, 1, 'Casado', 1, 'CARMEN ALVARADO', '3665-5129',
            '', 'ACTIVO'
        ),
        (
            '2022-02-21', 'KARLA PAZ CHÁVEZ', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2346-9754', '3668-6654', '1768333280103', '3897215-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'SUPERVISOR DE CALL CENTER', 'LOCAL', 'Guatemala',
            '', 'GTQ', 5600.00, 'Mensual', 1, 1, 1, 'Soltera', 1, '', '',
            '', 'ACTIVO'
        ),
        (
            '2024-07-03', 'MIGUEL MORALES ALVARADO', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2361-5652', '4234-1775', '2257261930103', '1239847-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 3850.00, 'Mensual', 1, 1, 0, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2021-11-19', 'ERICK GARCÍA GARCÍA', 'SANTA CATARINA PINULA, GUATEMALA',
            '2450-8027', '3740-6607', 'E78658930', '6191456-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'EJECUTIVO DE VENTAS', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1900.00, 'Mensual', 1, 1, 1, 'Unido', 2, 'DIANA GARCÍA', '4916-7595',
            '', 'ACTIVO'
        ),
        (
            '2024-10-02', 'LUIS CHÁVEZ CHÁVEZ', 'VILLA NUEVA, GUATEMALA',
            '2274-8750', '4223-6831', '2907994150101', '2141386-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'CONTADOR', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7750.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2021-03-13', 'PATRICIA MORALES HERNÁNDEZ', 'VILLA NUEVA, GUATEMALA',
            '2301-5940', '3415-8058', '1157791430901', '4900784-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 3550.00, 'Mensual', 1, 1, 0, 'Soltera', 1, '', '',
            '', 'ACTIVO'
        ),
        (
            '2022-03-08', 'ILSY VÁSQUEZ SANDOVAL', 'MIXCO, GUATEMALA',
            '2358-7656', '4961-8449', 'F35813421', '820013-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'EJECUTIVO DE VENTAS', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2450.00, 'Mensual', 1, 1, 1, 'Casada', 0, 'CARLOS VÁSQUEZ', '4953-8608',
            '', 'ACTIVO'
        ),
        (
            '2019-12-22', 'LUIS CIFUENTES VÁSQUEZ', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2261-1903', '5986-3121', '2287649090101', '4246391-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'ENCARGADO DE RECURSOS HUMANOS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7850.00, 'Mensual', 1, 1, 1, 'Unido', 2, 'GLORIA CIFUENTES', '4728-5426',
            '', 'ACTIVO'
        ),
        (
            '2024-02-25', 'PEDRO PAZ ROMERO', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2336-5364', '4108-3938', '2883778670301', '6656975-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'SUPERVISOR DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6850.00, 'Mensual', 1, 1, 1, 'Unido', 2, 'ILSY PAZ', '2856-1007',
            '', 'ACTIVO'
        ),
        (
            '2022-01-25', 'MARÍA AGUILAR LÓPEZ', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2255-8269', '3303-3553', '1536124440101', '8366988-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'ANALISTA DE MERCADEO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6500.00, 'Mensual', 1, 1, 1, 'Casada', 0, 'EDUARDO AGUILAR', '5133-4267',
            '', 'ACTIVO'
        ),
        (
            '2020-01-08', 'LETICIA CONTRERAS ALVARADO', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2219-1815', '4105-4377', 'B14635110', '157808-0', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'COORDINADOR DE MARCA', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2200.00, 'Mensual', 1, 1, 1, 'Casada', 1, 'ROBERTO CONTRERAS', '3873-8259',
            '', 'ACTIVO'
        ),
        (
            '2020-07-15', 'MARVIN PÉREZ MENDOZA', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2461-2533', '3894-8360', '2002158830101', '8061139-0', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'EJECUTIVO DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6400.00, 'Mensual', 1, 1, 1, 'Casado', 3, 'VERÓNICA PÉREZ', '3698-3777',
            '', 'ACTIVO'
        ),
        (
            '2024-02-17', 'BYRON MARTÍNEZ BARRIOS', 'SAN MIGUEL PETAPA, GUATEMALA',
            '2262-7026', '5995-2965', '1251268950901', '2370703-9', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'DISEÑADOR GRÁFICO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6050.00, 'Mensual', 1, 1, 1, 'Unido', 0, 'ANDREA MARTÍNEZ', '5123-7596',
            '', 'ACTIVO'
        ),
        (
            '2022-04-09', 'ALEJANDRO MORALES ESCOBAR', 'CARRETERA A EL SALVADOR, KM 16',
            '2270-5361', '3566-3638', 'F16768259', '6409236-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'EJECUTIVO DE VENTAS', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2150.00, 'Mensual', 1, 1, 1, 'Casado', 3, 'ILSY MORALES', '3629-3784',
            '', 'ACTIVO'
        ),
        (
            '2019-12-10', 'VERÓNICA LEMUS RODRÍGUEZ', 'SANTA CATARINA PINULA, GUATEMALA',
            '2406-3672', '5329-8652', '1632927500102', '523545-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7950.00, 'Mensual', 1, 1, 1, 'Unida', 2, 'CARLOS LEMUS', '5161-2967',
            '', 'ACTIVO'
        ),
        (
            '2022-09-02', 'KEVIN REYES ESCOBAR', 'MIXCO, GUATEMALA',
            '2319-4785', '5740-3346', '1500510000101', '5853232-2', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4150.00, 'Mensual', 1, 1, 0, 'Soltero', 1, '', '',
            '', 'ACTIVO'
        ),
        (
            '2019-04-17', 'OSCAR BARRIOS HERNÁNDEZ', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2405-1997', '4142-1325', 'G08219612', '2892655-2', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'ANALISTA DE MERCADEO', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1300.00, 'Mensual', 1, 1, 1, 'Casado', 3, 'SANDRA BARRIOS', '5715-6478',
            '', 'ACTIVO'
        ),
        (
            '2019-04-28', 'CARMEN CONTRERAS CASTILLO', 'CHINAUTLA, GUATEMALA',
            '2261-1856', '5820-1865', '2304520170101', '7412562-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'AUXILIAR CONTABLE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4850.00, 'Mensual', 1, 1, 0, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2021-02-14', 'MARVIN MARTÍNEZ CHÁVEZ', 'ZONA 18, CIUDAD DE GUATEMALA',
            '2483-7015', '3708-7658', '1927408610301', '9249726-0', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7700.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2019-03-04', 'ILSY MARTÍNEZ LÓPEZ', 'SANTA CATARINA PINULA, GUATEMALA',
            '2281-1030', '4835-2930', '1592331930103', '1511673-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'ILUSTRADOR DIGITAL', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4050.00, 'Mensual', 1, 1, 0, 'Unida', 1, 'WILLIAM MARTÍNEZ', '4940-2913',
            '', 'ACTIVO'
        ),
        (
            '2024-09-22', 'RICARDO PÉREZ PAZ', 'VILLA NUEVA, GUATEMALA',
            '2304-9010', '5575-8954', 'B35212223', '6738050-0', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2500.00, 'Mensual', 1, 1, 1, 'Casado', 0, 'WENDY PÉREZ', '4275-5688',
            '', 'ACTIVO'
        ),
        (
            '2025-02-21', 'ALEJANDRO CASTILLO REYES', 'CHINAUTLA, GUATEMALA',
            '2450-6086', '4849-8284', '2831664200103', '6876590-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'DISEÑADOR UX/UI', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6350.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2023-07-12', 'GLORIA SOLÍS RAMÍREZ', 'VILLA NUEVA, GUATEMALA',
            '2205-7767', '3445-7998', '2394127740103', '4545146-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4350.00, 'Mensual', 1, 1, 0, 'Casada', 1, 'BYRON SOLÍS', '5906-3731',
            '', 'ACTIVO'
        ),
        (
            '2022-09-08', 'MARVIN ALVARADO PÉREZ', 'SANTA CATARINA PINULA, GUATEMALA',
            '2415-7373', '5104-8821', 'G94037205', '5787962-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'ADMINISTRADOR DE BASE DE DATOS', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1700.00, 'Mensual', 1, 1, 1, 'Unido', 3, 'WENDY ALVARADO', '2518-5948',
            '', 'ACTIVO'
        ),
        (
            '2019-10-21', 'DIANA ESTRADA RODRÍGUEZ', 'CARRETERA A EL SALVADOR, KM 16',
            '2409-6443', '3843-9155', '2764324030102', '1583736-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 9650.00, 'Mensual', 1, 1, 1, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2025-01-28', 'MARVIN CRUZ REYES', 'ZONA 7, CIUDAD DE GUATEMALA',
            '2208-2433', '5922-7952', '3086267470102', '2529012-9', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR BACKEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7600.00, 'Mensual', 1, 1, 1, 'Unido', 2, 'ANDREA CRUZ', '3610-9461',
            '', 'ACTIVO'
        ),
        (
            '2019-07-23', 'ILSY BARRIOS LEMUS', 'SAN MIGUEL PETAPA, GUATEMALA',
            '2425-8334', '5262-2387', 'H74664323', '4907093-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'DISEÑADOR UX/UI', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1550.00, 'Mensual', 1, 1, 1, 'Casada', 1, 'RICARDO BARRIOS', '4552-7457',
            '', 'ACTIVO'
        ),
        (
            '2020-12-14', 'WENDY SANDOVAL RODRÍGUEZ', 'CHINAUTLA, GUATEMALA',
            '2461-7827', '5260-3725', '1886320600101', '7909795-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR BACKEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7800.00, 'Mensual', 1, 1, 1, 'Casada', 1, 'JOSÉ SANDOVAL', '3678-5474',
            '', 'ACTIVO'
        ),
        (
            '2020-01-16', 'LUIS ORTIZ REYES', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2287-6509', '4428-9124', '2531295860501', '9646799-8', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 1, 'DESARROLLADOR FRONTEND', 'LOCAL', 'Guatemala',
            '', 'GTQ', 9950.00, 'Mensual', 1, 1, 1, 'Casado', 3, 'LUCÍA ORTIZ', '5814-7622',
            '', 'ACTIVO'
        ),
        (
            '2025-02-03', 'CARMEN CRUZ SANDOVAL', 'ANTIGUA GUATEMALA, SACATEPÉQUEZ',
            '2391-5701', '4133-8047', '2059512300101', '6153425-K', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'CONTADOR', 'LOCAL', 'Guatemala',
            '', 'GTQ', 7700.00, 'Mensual', 1, 1, 1, 'Unida', 2, 'ALEJANDRO CRUZ', '2128-8509',
            '', 'ACTIVO'
        ),
        (
            '2024-04-15', 'LETICIA MENDOZA PÉREZ', 'ZONA 5, CIUDAD DE GUATEMALA',
            '2369-7896', '3115-2153', 'D31560408', '1144706-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'ASESOR COMERCIAL', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 900.00, 'Mensual', 1, 1, 1, 'Unida', 2, 'RICARDO MENDOZA', '4416-7207',
            '', 'ACTIVO'
        ),
        (
            '2024-03-12', 'WENDY ROMERO CONTRERAS', 'ZONA 18, CIUDAD DE GUATEMALA',
            '2492-1639', '5724-3691', '1548190540101', '1211751-8', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'ASESOR COMERCIAL', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4250.00, 'Mensual', 1, 1, 0, 'Unida', 0, 'RICARDO ROMERO', '4355-2240',
            '', 'ACTIVO'
        ),
        (
            '2025-02-14', 'SILVIA CHÁVEZ RAMÍREZ', 'CARRETERA A EL SALVADOR, KM 16',
            '2347-3312', '4572-5972', '2821842130103', '4554704-8', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'ILUSTRADOR DIGITAL', 'LOCAL', 'Guatemala',
            '', 'GTQ', 5200.00, 'Mensual', 1, 1, 1, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2023-07-23', 'VERÓNICA ESTRADA LÓPEZ', 'ZONA 7, CIUDAD DE GUATEMALA',
            '2333-1474', '5452-7536', 'G25284561', '1465412-3', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'ANALISTA DE MERCADEO', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2050.00, 'Mensual', 1, 1, 1, 'Casada', 3, 'EDUARDO ESTRADA', '2520-5696',
            '', 'ACTIVO'
        ),
        (
            '2022-10-03', 'ILSY CHÁVEZ SOLÍS', 'ANTIGUA GUATEMALA, SACATEPÉQUEZ',
            '2313-1463', '4380-8540', '1856422630101', '7668636-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'ASISTENTE ADMINISTRATIVO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 4450.00, 'Mensual', 1, 1, 0, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2023-07-27', 'ERICK ESTRADA CHÁVEZ', 'ZONA 18, CIUDAD DE GUATEMALA',
            '2318-5142', '3952-7980', '2262456050101', '5368414-6', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'AGENTE DE ATENCIÓN AL CLIENTE', 'LOCAL', 'Guatemala',
            '', 'GTQ', 3200.00, 'Mensual', 1, 1, 0, 'Casado', 0, 'KARLA ESTRADA', '3940-6918',
            '', 'ACTIVO'
        ),
        (
            '2019-03-28', 'JOSÉ ESTRADA LÓPEZ', 'ANTIGUA GUATEMALA, SACATEPÉQUEZ',
            '2206-4038', '5955-5396', 'H81724664', '9292412-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'ANALISTA DE MERCADEO', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2000.00, 'Mensual', 1, 1, 1, 'Casado', 2, 'DIANA ESTRADA', '2928-3574',
            '', 'ACTIVO'
        ),
        (
            '2022-09-17', 'CLAUDIA CIFUENTES SOLÍS', 'MIXCO, GUATEMALA',
            '2461-5155', '5688-7596', '3189183340901', '2114293-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'ANALISTA FINANCIERO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 8800.00, 'Mensual', 1, 1, 1, 'Unida', 3, 'ERICK CIFUENTES', '4424-9032',
            '', 'ACTIVO'
        ),
        (
            '2024-12-22', 'MARÍA BARRIOS ORTIZ', 'SANTA CATARINA PINULA, GUATEMALA',
            '2450-1964', '5659-9092', '3167350290301', '8526001-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'SUPERVISOR DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 8050.00, 'Mensual', 1, 1, 1, 'Casada', 0, 'ROBERTO BARRIOS', '3367-5981',
            '', 'ACTIVO'
        ),
        (
            '2020-01-03', 'SILVIA ALVARADO MORALES', 'ZONA 1, CIUDAD DE GUATEMALA',
            '2426-3799', '3731-1895', '2140155140102', '3530872-5', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 5, 'GERENTE ADMINISTRATIVO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 11600.00, 'Mensual', 1, 1, 1, 'Soltera', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2020-10-07', 'ANA CONTRERAS MÉNDEZ', 'CARRETERA A EL SALVADOR, KM 16',
            '2271-8306', '3593-5596', 'F79101699', '5373905-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'SUPERVISOR DE CALL CENTER', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1950.00, 'Mensual', 1, 1, 1, 'Casada', 1, 'ALEJANDRO CONTRERAS', '2221-6313',
            '', 'ACTIVO'
        ),
        (
            '2021-08-07', 'LETICIA ALVARADO HERNÁNDEZ', 'CHINAUTLA, GUATEMALA',
            '2314-2493', '3874-5430', '2253733050101', '6313185-2', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 4, 'SUPERVISOR DE CALL CENTER', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6500.00, 'Mensual', 1, 1, 1, 'Unida', 3, 'MARVIN ALVARADO', '2331-3844',
            '', 'ACTIVO'
        ),
        (
            '2025-07-09', 'KARLA SANDOVAL SANDOVAL', 'ZONA 12, CIUDAD DE GUATEMALA',
            '2466-3618', '4947-4364', '1912151870501', '2148220-4', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'CONTADOR', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6850.00, 'Mensual', 1, 1, 1, 'Casada', 1, 'ALEJANDRO SANDOVAL', '2909-9385',
            '', 'ACTIVO'
        ),
        (
            '2020-06-23', 'JOSÉ CHÁVEZ CASTILLO', 'ANTIGUA GUATEMALA, SACATEPÉQUEZ',
            '2212-5883', '5246-7478', 'E15866271', '6288428-1', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 6, 'COORDINADOR DE MARCA', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 2400.00, 'Mensual', 1, 1, 1, 'Soltero', 1, '', '',
            '', 'ACTIVO'
        ),
        (
            '2024-10-02', 'ROBERTO RODRÍGUEZ VÁSQUEZ', 'CHINAUTLA, GUATEMALA',
            '2441-2220', '3829-6912', '3216408410103', '2552884-8', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 7, 'ANALISTA FINANCIERO', 'LOCAL', 'Guatemala',
            '', 'GTQ', 8150.00, 'Mensual', 1, 1, 1, 'Soltero', 0, '', '',
            '', 'ACTIVO'
        ),
        (
            '2019-11-02', 'OSCAR GARCÍA MENDOZA', 'SANTA CATARINA PINULA, GUATEMALA',
            '2234-6113', '4434-6977', '3092391630101', '5605264-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 3, 'EJECUTIVO DE VENTAS', 'LOCAL', 'Guatemala',
            '', 'GTQ', 6400.00, 'Mensual', 1, 1, 1, 'Casado', 1, 'PATRICIA GARCÍA', '4634-9786',
            '', 'ACTIVO'
        ),
        (
            '2020-01-26', 'CARLOS ROMERO CIFUENTES', 'ZONA 18, CIUDAD DE GUATEMALA',
            '2201-7958', '3731-3083', 'A89823384', '2496700-7', 'NINGUNA', 'NINGUNA',
            'TECNIMARKET S.A. DE GUATEMALA', 2, 'DISEÑADOR GRÁFICO', 'EXTRANJERO', 'Estados Unidos',
            'Visa V-3', 'USD', 1950.00, 'Mensual', 1, 1, 1, 'Casado', 2, 'GLORIA ROMERO', '4418-4905',
            '', 'ACTIVO'
        ),
    ])
 
    cursor.executemany("""
    INSERT OR IGNORE INTO empleado (
        fecha_ingreso, nombre, direccion, telefono, celular, dpi, nit,
        senales, enfermedad, empresa, departamento_id, cargo, tipo_origen, pais,
        visa, moneda, sueldo_base, tipo_pago, aplica_igss, aplica_bono, aplica_isr,
        estado_civil, hijos, conyuge, tel_conyuge, foto, estado
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, empleados)
    
    conn.commit()
    conn.close()