import os
import re
from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.guatemala_rules import calcular_planilla_empleado
from app.db import init_db, get_db_connection

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_desarrollo_secreta_gt_2026')

    # Inicializar la base de datos dentro del contexto de aplicación
    with app.app_context():
        init_db()

    # --- RUTA PRINCIPAL ---
    @app.route('/', methods=['GET', 'POST'])
    def inicio():
        resultado = None
        if request.method == 'POST':
            nombre = request.form.get('nombre')
            departamento = request.form.get('departamento')
            sueldo = float(request.form.get('sueldo', 0))
            dias = int(request.form.get('dias', 30))
            moneda = request.form.get('moneda')
            tipo_cambio = float(request.form.get('tipo_cambio', 7.80))

            es_dolares = (moneda == 'USD')
            calculos = calcular_planilla_empleado(sueldo, dias, es_dolares, tipo_cambio)
            
            resultado = {
                'nombre': nombre,
                'departamento': departamento,
                'moneda': moneda,
                'calculos': calculos
            }

        return render_template('index.html', resultado=resultado)

    # =========================================================
    # 1. API EMPLEADOS (OBTENER Y GUARDAR)
    # =========================================================
    @app.route('/api/empleados', methods=['GET'])
    def obtener_empleados():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, d.nombre as departamento 
            FROM empleado e 
            LEFT JOIN departamento d ON e.departamento_id = d.id 
            WHERE e.estado = 'ACTIVO'
        """)
        empleados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(empleados), 200

    def formatear_telefono(numero):
        if not numero:
            return ""
        digitos = ''.join(filter(str.isdigit, str(numero)))[:8]
        if len(digitos) > 4:
            return f"{digitos[:4]}-{digitos[4:]}"
        return digitos

    @app.route('/api/empleados', methods=['POST'])
    def guardar_empleado():
        data = request.get_json(silent=True) or {}
        dpi = data.get('dpi')
        if not dpi:
            return jsonify({"status": "error", "message": "El DPI es obligatorio"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Buscar ID del departamento por su nombre
        depto_nombre = data.get('departamento')
        cursor.execute("SELECT id FROM departamento WHERE nombre = ?", (depto_nombre,))
        depto_row = cursor.fetchone()
        depto_id = depto_row['id'] if depto_row else None

        # Formateo garantizado antes de insertar/actualizar en BD
        tel_fijo = formatear_telefono(data.get('telefono'))
        celular = formatear_telefono(data.get('celular'))
        tel_conyuge = formatear_telefono(data.get('telConyuge'))

        try:
            cursor.execute("""
                INSERT INTO empleado (
                    dpi, fecha_ingreso, nombre, direccion,
                    telefono, celular, nit, senales, enfermedad, empresa,
                    departamento_id, cargo, tipo_origen, pais, visa, moneda,
                    sueldo_base, tipo_pago, aplica_igss, aplica_bono, aplica_isr,
                    estado_civil, hijos, conyuge, tel_conyuge, foto, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVO')
                ON CONFLICT(dpi) DO UPDATE SET
                    fecha_ingreso=excluded.fecha_ingreso,
                    nombre=excluded.nombre,
                    direccion=excluded.direccion,
                    telefono=excluded.telefono,
                    celular=excluded.celular,
                    nit=excluded.nit,
                    senales=excluded.senales,
                    enfermedad=excluded.enfermedad,
                    departamento_id=excluded.departamento_id,
                    cargo=excluded.cargo,
                    tipo_origen=excluded.tipo_origen,
                    pais=excluded.pais,
                    visa=excluded.visa,
                    moneda=excluded.moneda,
                    sueldo_base=excluded.sueldo_base,
                    tipo_pago=excluded.tipo_pago,
                    aplica_igss=excluded.aplica_igss,
                    aplica_bono=excluded.aplica_bono,
                    aplica_isr=excluded.aplica_isr,
                    estado_civil=excluded.estado_civil,
                    hijos=excluded.hijos,
                    conyuge=excluded.conyuge,
                    tel_conyuge=excluded.tel_conyuge,
                    foto=excluded.foto
            """, (
                dpi, data.get('fecha'), data.get('nombre'), data.get('direccion'),
                tel_fijo, celular, data.get('nit'),
                data.get('senales'), data.get('enfermedad'), data.get('empresa'),
                depto_id, data.get('cargo'), data.get('tipoOrigen', 'LOCAL'), data.get('pais', 'Guatemala'),
                data.get('visa'), data.get('moneda', 'GTQ'), float(data.get('sueldo', 0)),
                data.get('tipoPago', 'Mensual'), 1 if data.get('aplicaIgss') else 0,
                1 if data.get('aplicaBono') else 0, 1 if data.get('aplicaIsr') else 0,
                data.get('estadoCivil'), int(data.get('hijos', 0)), data.get('conyuge'),
                tel_conyuge, data.get('foto')
            ))
            conn.commit()
            return jsonify({"status": "success", "message": "Empleado guardado en Base de Datos"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            conn.close()

    # =========================================================
    # 2. API DEPARTAMENTOS
    # =========================================================
    @app.route('/api/departamentos', methods=['GET'])
    def obtener_departamentos():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM departamento")
        deptos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(deptos), 200

    @app.route('/api/departamentos', methods=['POST'])
    def agregar_departamento():
        data = request.get_json(silent=True) or {}
        codigo = data.get('codigo')
        nombre = data.get('nombre')
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO departamento (codigo, nombre) VALUES (?, ?)", (codigo, nombre))
            conn.commit()
            return jsonify({"status": "success"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/departamentos/<int:id>', methods=['DELETE'])
    def eliminar_departamento(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM departamento WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200

    # =========================================================
    # 1. API EMPLEADOS (OBTENER, BUSCAR Y GUARDAR)
    # =========================================================
    @app.route('/api/empleados/buscar', methods=['GET'])
    def api_buscar_empleado():
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify([]), 200

        termino_limpio = re.sub(r'[\s-]', '', q)
        conn = get_db_connection()
        cursor = conn.cursor()

        # Si tiene 9 caracteres -> Búsqueda por Pasaporte / Extranjero
        if len(termino_limpio) == 9:
            cursor.execute("""
                SELECT e.*, d.nombre as departamento 
                FROM empleado e
                LEFT JOIN departamento d ON e.departamento_id = d.id
                WHERE REPLACE(REPLACE(e.dpi, '-', ''), ' ', '') = ?
                  AND (UPPER(e.tipo_origen) = 'EXTRANJERO' OR e.pais != 'Guatemala')
                  AND e.estado = 'ACTIVO'
            """, (termino_limpio,))
            resultados = cursor.fetchall()
            if resultados:
                conn.close()
                return jsonify([dict(row) for row in resultados]), 200

        # Si tiene 13 dígitos -> Búsqueda por DPI / Local
        elif len(termino_limpio) == 13 and termino_limpio.isdigit():
            cursor.execute("""
                SELECT e.*, d.nombre as departamento 
                FROM empleado e
                LEFT JOIN departamento d ON e.departamento_id = d.id
                WHERE REPLACE(REPLACE(e.dpi, '-', ''), ' ', '') = ?
                  AND (UPPER(e.tipo_origen) = 'LOCAL' OR e.pais = 'Guatemala')
                  AND e.estado = 'ACTIVO'
            """, (termino_limpio,))
            resultados = cursor.fetchall()
            if resultados:
                conn.close()
                return jsonify([dict(row) for row in resultados]), 200

        # Búsqueda general (por coincidencia parcial en nombre, DPI/Pasaporte o NIT)
        param = f"%{termino_limpio.lower()}%"
        cursor.execute("""
            SELECT e.*, d.nombre as departamento 
            FROM empleado e
            LEFT JOIN departamento d ON e.departamento_id = d.id
            WHERE (
                LOWER(REPLACE(REPLACE(e.dpi, '-', ''), ' ', '')) LIKE ? OR
                LOWER(e.nombre) LIKE ? OR
                LOWER(REPLACE(REPLACE(e.nit, '-', ''), ' ', '')) LIKE ?
            )
            AND e.estado = 'ACTIVO'
        """, (param, f"%{q.lower()}%", param))
        
        resultados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(resultados), 200

    # =========================================================
    # 3. API ASISTENCIA
    # =========================================================
    @app.route('/api/asistencia', methods=['GET'])
    def obtener_asistencia():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM asistencia")
        registros = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(registros), 200

    @app.route('/api/asistencia', methods=['POST'])
    def guardar_asistencia():
        data = request.get_json(silent=True) or []
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            for item in data:
                cursor.execute("""
                    INSERT INTO asistencia (
                        empleado_dpi, fecha, horas_extra, tarifa_extra, aplica_pago, total_extra
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item['dpi'], item['fecha'], item['horasExtra'],
                    item['tarifa'], 1 if item['aplicaPago'] else 0, item['montoTotal']
                ))
            conn.commit()
            return jsonify({"status": "success"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            conn.close()

    # =========================================================
    # 4. API BAJAS Y EX-EMPLEADOS
    # =========================================================
    @app.route('/api/baja', methods=['POST'])
    def procesar_baja_empleado():
        data = request.get_json(silent=True) or {}
        raw_dpi = data.get('dpi', '')
        dpi = raw_dpi.replace(' ', '').replace('-', '') if raw_dpi else None
        
        if not dpi:
            return jsonify({"status": "error", "message": "El DPI es requerido"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO ex_empleado (
                    dpi, codigo, nombre, departamento, cargo, 
                    causal_salida, fecha_salida, monto_liquidado, foto
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dpi, data.get('codigo'), data.get('nombre'), data.get('departamento'),
                data.get('cargo'), data.get('causalSalida'), data.get('fechaSalida'),
                data.get('montoLiquidado'), data.get('foto')
            ))
            cursor.execute("DELETE FROM empleado WHERE dpi = ?", (dpi,))
            conn.commit()
            return jsonify({"status": "success", "message": "Empleado trasladado a ex_empleado exitosamente"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/ex-empleados', methods=['GET'])
    def obtener_ex_empleados():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ex_empleado ORDER BY fecha_registro DESC")
        ex_empleados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(ex_empleados), 200

    # API: ELIMINAR PERMANENTEMENTE UN EX-EMPLEADO DE LA BASE DE DATOS
    @app.route('/api/ex-empleados/<dpi>', methods=['DELETE'])
    def eliminar_ex_empleado_db(dpi):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM ex_empleado WHERE dpi = ?", (dpi,))
            conn.commit()
            return jsonify({"status": "success", "message": "Ex-empleado eliminado permanentemente de la BD"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/ex-empleados/<dpi>', methods=['DELETE'])
    def eliminar_ex_empleado(dpi):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ex_empleado WHERE dpi = ?", (dpi,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200

    # =========================================================
    # 5. API USUARIOS Y AUTENTICACIÓN
    # =========================================================
    @app.route('/api/login', methods=['POST'])
    def login_backend():
        data = request.get_json(silent=True) or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({"status": "error", "message": "Credenciales incompletas"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuario WHERE username = ? AND activo = 1", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            user_dict = dict(user)
            user_dict.pop('password', None)
            user_dict.pop('pass_admin_auth', None)
            return jsonify({"status": "success", "usuario": user_dict}), 200

        return jsonify({"status": "error", "message": "Usuario o contraseña incorrectos"}), 401

    @app.route('/api/perfil/actualizar', methods=['POST'])
    def actualizar_perfil_admin():
        data = request.get_json(silent=True) or {}
        username = data.get('username')
        correo = data.get('correo')
        telefono = data.get('telefono')
        password = data.get('password')
        pass_admin_auth = data.get('pass_admin_auth')

        if not username or not password:
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400

        hashed_password = generate_password_hash(password)
        hashed_admin_auth = generate_password_hash(pass_admin_auth) if pass_admin_auth else hashed_password

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE usuario 
                SET correo = ?, telefono = ?, password = ?, pass_admin_auth = ?
                WHERE username = ? AND rol = 'ADMIN'
            """, (correo, telefono, hashed_password, hashed_admin_auth, username))
            
            conn.commit()
            return jsonify({"status": "success", "message": "Perfil actualizado de forma segura"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
        finally:
            conn.close()

    # MANEJADORES DE ERROR HTTP
    @app.errorhandler(404)
    def recurso_no_encontrado(e):
        return jsonify({"status": "error", "message": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def error_interno_servidor(e):
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

    return app