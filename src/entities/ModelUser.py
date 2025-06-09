from flask import flash, request
from .models.User import User
from werkzeug.utils import secure_filename
import os

class ModelUser:

    @classmethod
    def get_by_id(cls,db,id):
        try: 

            cur = db.connection.cursor()
            cur.execute("SELECT * FROM admin WHERE id = %s", (id,))
            data = cur.fetchone()

            if data:
                id = data[0]
                nombre = data[1]
                email = data[2]
                
                user = User(id, nombre, None, email)


                return user
            return None
        except Exception as e:
            print(e)


    @classmethod
    def register(cls, db, nombre, correo, contraseña, es_super_admin=False):
        try:
            cursor = db.connection.cursor()

            # Verificar si el correo ya existe
            cursor.execute("SELECT * FROM admin WHERE email = %s", (correo,))
            resultado = cursor.fetchone()

            if resultado is not None:
                print("Error: El correo ya está registrado en admin.")
                cursor.close()
                return False

            # Hashear la contraseña
            hashed_password = User.hash_password(contraseña)

            print(f"Contraseña hasheada: {hashed_password}")

            # Insertar el nuevo administrador
            cursor.execute(
                "INSERT INTO admin (nombre, email, contraseña, fecha_creacion, es_super_admin) "
                "VALUES (%s, %s, %s, NOW(), %s)",
                (nombre, correo, hashed_password, int(es_super_admin))
            )

            db.connection.commit()
            cursor.close()

            return True
        except Exception as e:
            print("Error al registrar administrador:", e)
            try:
                cursor.close()
            except:
                pass
            return False


    @classmethod
    def login(cls,db,email,password):
        try:
            cur = db.connection.cursor()
            cur.execute("SELECT * FROM admin WHERE email = %s", (email,))
            data = cur.fetchone()

            if data:
                id = data[0]
                nombre = data[1]
                email = data[2]
                hashed_password = data[3]

                valor = User.check_password(hashed_password,password)
                if valor:
                    
                    user = User(id, None, None, email)
                    
                    return user
                return flash("error password")
            
        except Exception as e:
            print(e)

    # funcion para añadir el coche
    @classmethod
    def agregar_coche(cls, db, marca, modelo, anio, precio_contado, precio_financiado, estado, descripcion,
                    motor, consumo, cambio, combustible,
                    kilometros, puertas, plazas,tipo):
        try:
            cur = db.connection.cursor()
            cur.execute("""
                INSERT INTO coches 
                (marca, modelo, anio, precio_financiado, estado, descripcion, fecha_agregado,
                motor, precio_contado, consumo, cambio, combustible,
                kilometros, puertas, plazas,tipo)
                VALUES (%s, %s, %s, %s, %s,
                        %s, NOW(), %s, %s, %s, %s, %s,
                        %s, %s, %s,%s)
            """, (
                marca, modelo, anio, precio_financiado, estado, descripcion,
                motor, precio_contado, consumo, cambio, combustible,
                kilometros, puertas, plazas,tipo
            ))
            db.connection.commit()
            coche_id = cur.lastrowid
            cur.close()
            return coche_id

        except Exception as e:
            print("Error al insertar coche:", e)
            return None

    @classmethod
    def obtener_coches(cls,db):
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM coches WHERE EXISTS (SELECT 1 FROM fotos WHERE fotos.coche_id = coches.id)")
        coche = cur.fetchall()
        cur.close()
        
        return coche
    
    @classmethod
    def enviar_contacto(cls,db,nombre,email,telefono,motivo,descripcion):
        try:
            cur = db.connection.cursor()
            cur.execute("INSERT INTO mensajes (nombre,email,telefono,motivo,descripcion) VALUES (%s,%s,%s,%s,%s)",(nombre,email,telefono,motivo,descripcion))
            db.connection.commit()
            cur.close()

            return True

        except Exception as e:
            print(e)
    @classmethod
    def obtener_mensajes(cls,db):
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM mensajes")
        mensajes = cursor.fetchall()
        cursor.close()
        return mensajes
    
    @classmethod
    def eliminar_mensaje(cls,db,id):
        try:
            cursor = db.connection.cursor()
            cursor.execute("DELETE FROM mensajes WHERE id = %s", (id,))
            db.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(e)
            return False
        
    @classmethod
    def eliminar_coche(cls,db,id):
        try:
            cursor = db.connection.cursor()
            cursor.execute("DELETE FROM coches WHERE id = %s", (id,))
            db.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(e)
            return False
    @classmethod
    def obtener_coches_con_foto_principal(cls,db):
        try:
            cursor = db.connection.cursor()
            cursor.execute("""
                SELECT 
                    c.*, f.ruta
                FROM coches c
                LEFT JOIN (
                    SELECT coche_id, MIN(id) as min_foto_id
                    FROM fotos
                    GROUP BY coche_id
                ) primera_foto
                            ON c.id = primera_foto.coche_id
                LEFT JOIN fotos f ON f.id = primera_foto.min_foto_id
            """)
            coches = cursor.fetchall()
            cursor.close()
            return coches
        except Exception as e:
            print("Error:", e)
            return []

    @classmethod
    def obtener_coche(cls,db,id):
        try:
            cursor = db.connection.cursor()
            cursor.execute("SELECT * FROM coches WHERE id = %s", (id,))
            coche = cursor.fetchone()
            columnas = [col[0] for col in cursor.description]
            cursor.close()
            return coche, columnas
        except Exception as e:
            print(e)
            return None
    @classmethod
    def obtener_fotos(cls,db,id):
        try:
            cursor = db.connection.cursor()
            cursor.execute("SELECT ruta FROM fotos WHERE coche_id = %s", (id,))
            fotos = cursor.fetchall()
            cursor.close()
            return fotos
        except Exception as e:
            print(e)
            return None
    @classmethod
    def todas_fotos(cls,db):
        try:
            cursor = db.connection.cursor()
            cursor.execute("SELECT ruta FROM fotos")
            fotos = cursor.fetchall()
            cursor.close()
            return fotos
        except Exception as e:
            print(e)
            return None

    @classmethod
    def obtener_coches_con_foto_principal_paginados(cls, db, marca='', precio_min='', precio_max='', 
                                                anio_min='', anio_max='', combustible='', tipo='',cambio='',
                                                page=1, per_page=6):
        # Consulta SQL con orden explícito de columnas
        query = """
        SELECT SQL_CALC_FOUND_ROWS 
            c.id, c.marca, c.modelo, c.precio_contado, c.anio, c.combustible,
            (SELECT f.ruta FROM fotos f WHERE f.coche_id = c.id LIMIT 1) as ruta 
        FROM coches c
        WHERE 1=1
        """
        params = []
        
        # Aplicar filtros
        if marca:
            query += " AND c.marca = %s"
            params.append(marca)
        
        if precio_min:
            query += " AND c.precio_contado >= %s"
            params.append(float(precio_min))
        
        if precio_max:
            query += " AND c.precio_contado <= %s"
            params.append(float(precio_max))
        
        if anio_min:
            query += " AND c.anio >= %s"
            params.append(int(anio_min))
        
        if anio_max:
            query += " AND c.anio <= %s"
            params.append(int(anio_max))
        
        if combustible:
            query += " AND c.combustible = %s"
            params.append(combustible)

        if tipo:
            query += " AND c.tipo = %s"
            params.append(tipo)
        
        if cambio:
            query += " AND c.cambio = %s"
            params.append(cambio)

        # Paginación
        query += " LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])

        cursor = db.connection.cursor()
        cursor.execute(query, params)
        
        # Obtener resultados como tuplas
        coches_tuples = cursor.fetchall()
        
        # Obtener total de registros
        cursor.execute("SELECT FOUND_ROWS()")
        total = cursor.fetchone()[0]  # Acceder por índice
        cursor.close()

        return {
            'coches': coches_tuples,
            'total_pages': (total + per_page - 1) // per_page,
            'total_count': total
        }
    @classmethod
    def obtener_marcas_unicas(cls, db):
        cursor = db.connection.cursor()
        cursor.execute("SELECT DISTINCT marca FROM coches ORDER BY marca")
        # Acceder por índice (0 para la primera columna)
        marcas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return marcas

    @classmethod
    def obtener_combustibles_unicos(cls, db):
        cursor = db.connection.cursor()
        cursor.execute("SELECT DISTINCT combustible FROM coches ORDER BY combustible")
        # Acceder por índice (0 para la primera columna)
        combustibles = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return combustibles
    
    @classmethod
    def obtener_coche_por_id(cls, db, coche_id):
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM coches WHERE id = %s", (coche_id,))
        return cursor.fetchone()

    @classmethod
    def obtener_fotos_por_coche(cls, db, coche_id):
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM fotos WHERE coche_id = %s", (coche_id,))
        return cursor.fetchall()

    @classmethod
    def actualizar_coche(cls, db, coche_id, datos, nuevas_fotos=[]):
        cursor = db.connection.cursor()
        
        # Actualizar datos del coche
        query = """
        UPDATE coches 
        SET marca=%s, modelo=%s, estado=%s, precio_contado=%s, 
            precio_financiado=%s, anio=%s, consumo=%s, combustible=%s, 
            cambio=%s, kilometros=%s, puertas=%s, plazas=%s, 
            motor=%s, descripcion=%s,tipo=%s
        WHERE id=%s
        """
        params = (
            datos['marca'], datos['modelo'], datos['estado'],
            datos['precio_contado'], datos['precio_financiado'],
            datos['ano'], datos['consumo'], datos['combustible'],
            datos['cambio'], datos['kilometros'], datos['puertas'],
            datos['plazas'], datos['motor'], datos['comentario'],datos['tipo'],coche_id
        )
        cursor.execute(query, params)
        db.connection.commit()
        cursor.close()

    @classmethod
    def eliminar_foto(cls, db, foto_id):
        cursor = db.connection.cursor()
        cursor.execute("DELETE FROM fotos WHERE id = %s", (foto_id,))
        db.connection.commit()
    
    @staticmethod
    def obtener_tipos_unicos(db):
        cursor = db.connection.cursor()
        cursor.execute("SELECT DISTINCT tipo FROM coches WHERE tipo IS NOT NULL AND tipo != ''")
        tipos = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tipos

    @staticmethod
    def obtener_cambios_unicos(db):
        cursor = db.connection.cursor()
        cursor.execute("SELECT DISTINCT cambio FROM coches WHERE cambio IS NOT NULL AND cambio != ''")
        cambios = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return cambios