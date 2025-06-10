from flask import Flask, app, request, jsonify, render_template, redirect, url_for,flash, make_response, current_app,send_from_directory
from numpy import imag
from forms import loginform, contactsForm, registerform
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from config import config
from flask_mysqldb import MySQL
from entities.ModelUser import ModelUser
from utils.security import Security
from werkzeug.utils import secure_filename
from flask_toastr import Toastr
import os
import shutil




app = Flask(__name__)

app.config.from_object(config["dev"])

db = MySQL(app)

toastr = Toastr(app)


# Define la ruta absoluta donde Render monta el disco persistente
DISCO_RENDER = '/var/data'


login_manager = LoginManager(app)

@app.context_processor
def inject_toastr():
    return dict(toastr=toastr)

@login_manager.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)
        
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('/var/data/uploads', filename)

@app.route("/solicitudes", methods=["GET"])
def solicitudes():
    if not current_user.is_authenticated:
        return redirect("/")
    
    solicitudes = ModelUser.obtener_mensajes(db)
    return render_template("mensajes_admin.html", solicitudes=solicitudes)

@app.route("/register", methods=["GET", "POST"])
def register():
    registerForm = registerform()
    if request.method == "GET":
        if not current_user.is_authenticated:
            return redirect("/")
        return render_template("register.html", form=registerForm)

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["email"]
        contraseña = request.form["password"]
        es_super_admin = request.form.get("es_super_admin", False)
        
        if ModelUser.register(db, nombre, correo, contraseña, es_super_admin):
            flash("Usuario registrado con éxito", "success")
            return redirect(url_for("login"))
        else:
            flash("Error al registrar el usuario", "danger")

@app.route("/contacto", methods=["POST", "GET"])
def contacto():

    contactForm = contactsForm()
    
    if request.method == "POST":
            if contactForm.validate_on_submit():
                nombre = request.form["nombre"]
                email = request.form["email"]
                telefono = request.form["telefono"]
                motivo = request.form["motivo"]
                descripcion = request.form["descripcion"]
                
                ModelUser.enviar_contacto(db, nombre, email, telefono, motivo, descripcion)
                flash("Mensaje enviado con éxito", "success")
                return redirect(url_for("contacto"))
            else:
                flash("Error al enviar el mensaje", "danger")
                return render_template("contacto.html", form=contactForm)
    if request.method == "GET":
        return render_template("contacto.html", form=contactForm)

@app.route("/mensaje/<int:id>", methods=["GET"])
def eliminar_mensaje(id):
    if not current_user.is_authenticated:
        return redirect("/")
    
    ModelUser.eliminar_mensaje(db, id)
    flash("Mensaje eliminado con éxito", "success")
    return redirect(url_for("ver_mensajes"))

@app.route("/mensaje", methods=["GET"])
def ver_mensajes():
    if not current_user.is_authenticated:
        return redirect("/")
    
    mensajes = ModelUser.obtener_mensajes(db)
    
    return render_template("mensajes_admin.html", mensajes=mensajes)


@app.route("/somos", methods=["GET"])
def somos():
    return render_template("somos.html")

@app.route("/vender", methods=["GET"])
def vender():
    return render_template("vender.html")

@app.route("/coche/<id>", methods=["GET"])
def coche(id):
    obtener_coche = ModelUser.obtener_coche(db, id)
    obtener_fotos = ModelUser.obtener_fotos(db, id)

    if not obtener_coche:
        flash("Coche no encontrado", "warning")
        return redirect(url_for("home"))

    imagenes_limpias = [
    (f[0].replace("\\", "/") if f[0] else "img/no_image.jpg")
    for f in obtener_fotos
    ]

    datos = dict(zip(obtener_coche[1], obtener_coche[0]))
    
    return render_template("coche.html", datos=datos, images=imagenes_limpias)



@app.route("/", methods=["GET"])
def inicio():
    fotos = ModelUser.todas_fotos(db)
    
    images = [img[0] for img in fotos]

    return render_template("inicio.html", images=images)

@app.route("/catalogo", methods=["GET", "POST"])
def catalogo():
    # Obtener parámetros (POST tiene prioridad sobre GET)
    filtros = {
        'marca': request.form.get('marca', request.args.get('marca', '')),
        'precio_min': request.form.get('precio_contado_min', request.args.get('precio_contado_min', '')),
        'precio_max': request.form.get('precio_contado_max', request.args.get('precio_contado_max', '')),
        'anio_min': request.form.get('anio_min', request.args.get('anio_min', '')),
        'anio_max': request.form.get('anio_max', request.args.get('anio_max', '')),
        'combustible': request.form.get('combustible', request.args.get('combustible', '')),
        'tipo': request.form.get('tipo', request.args.get('tipo', '')),
        'cambio': request.form.get('cambio', request.args.get('cambio', ''))
    }
    
    # Paginación (siempre por GET)
    page = request.args.get('page', 1, type=int)
    per_page = 15

    # Obtener datos con filtros
    coches_data = ModelUser.obtener_coches_con_foto_principal_paginados(
        db,
        marca=filtros['marca'],
        precio_min=filtros['precio_min'],
        precio_max=filtros['precio_max'],
        anio_min=filtros['anio_min'],
        anio_max=filtros['anio_max'],
        combustible=filtros['combustible'],
        tipo=filtros['tipo'],
        cambio=filtros['cambio'],
        page=page,
        per_page=per_page
    )

    # Procesar imágenes
    coches_limpios = []
    for coche_tuple in coches_data['coches']:
        coche_list = list(coche_tuple)
        if coche_list[6]:  # ruta está en la posición 6
            coche_list[6] = coche_list[6].replace('\\', '/')
        else:
            coche_list[6] = "img/no_image.jpg"
        coches_limpios.append(coche_list)

    # Obtener opciones para filtros
    marcas = ModelUser.obtener_marcas_unicas(db)
    combustibles = ModelUser.obtener_combustibles_unicos(db)
    tipos = ModelUser.obtener_tipos_unicos(db)
    cambios = ModelUser.obtener_cambios_unicos(db)

    return render_template("catalogo.html",
                        coches=coches_limpios,
                        marcas=marcas,
                        combustibles=combustibles,
                        tipos=tipos,
                        cambios=cambios,
                        filtros_actuales=filtros,
                        pagination={
                            'page': page,
                            'pages': coches_data['total_pages'],
                            'total': coches_data['total_count'],
                            'per_page': per_page
                        })


@app.route('/panel/editar/<int:coche_id>', methods=['GET', 'POST'])
def editar_coche(coche_id):
    if request.method == 'POST':
        datos = request.form.to_dict()
        fotos = request.files.getlist('fotos[]')

        carpeta_final = os.path.join(DISCO_RENDER, 'uploads', str(coche_id))
        os.makedirs(carpeta_final, exist_ok=True)

        cursor = db.connection.cursor()
        for foto in fotos:
            if foto and foto.filename != '':
                filename = secure_filename(foto.filename)
                ruta_destino = os.path.join(carpeta_final, filename)

                try:
                    foto.save(ruta_destino)
                except Exception as e:
                    print(f"Error guardando imagen: {e}")

                # Guardamos la ruta relativa desde el disco para url_for('static', ...)
                ruta_relativa = os.path.join(str(coche_id), filename).replace('\\', '/')

                cursor.execute(
                    "INSERT INTO fotos (coche_id, ruta) VALUES (%s, %s)",
                    (coche_id, ruta_relativa)
                )

        db.connection.commit()
        ModelUser.actualizar_coche(db, coche_id, datos, fotos)
        flash('Coche actualizado correctamente', 'success')
        return redirect(url_for('panel'))

    else:
        coche = ModelUser.obtener_coche_por_id(db, coche_id)
        fotos = ModelUser.obtener_fotos_por_coche(db, coche_id)
        if not coche:
            flash('Coche no encontrado', 'warning')
            return redirect(url_for('panel_admin'))
        return render_template('editar_coche.html', coche=coche, fotos=fotos)


@app.route('/panel/eliminar-foto/<int:foto_id>', methods=['DELETE'])
def eliminar_foto(foto_id):
    ModelUser.eliminar_foto(db, foto_id)
    return jsonify({'success': True}), 200


@app.route("/login", methods=["GET", "POST"])
def login():
    loginForm = loginform()

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        logged_user = ModelUser.login(db, email, password)
        if logged_user:
            jwt_token = Security.generate_token(logged_user)
            login_user(logged_user)
            response = make_response(redirect(url_for("panel")))
            response.set_cookie("jwt_token", jwt_token, httponly=True, secure=True, samesite="Lax")
            return response
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html", form=loginForm)


@app.route("/panel", methods=["GET", "POST"])
def panel():
    token = request.cookies.get("jwt_token")
    has_access = Security.verify_token(token)

    if not has_access:
        flash("Sesion no válida. Inicia sesion nuevamente", "warning")
        return redirect(url_for("login"))

    if request.method == 'GET':
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        return render_template("panel.html")

    if request.method == "POST":
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        anio = request.form.get('ano')
        precio_contado = request.form.get('precio_contado')
        precio_financiado = request.form.get('precio_financiado')
        estado = request.form.get('estado')
        descripcion = request.form.get('comentario')
        motor = request.form.get('motor')
        consumo = request.form.get('consumo')
        cambio = request.form.get('cambio')
        combustible = request.form.get('combustible')
        kilometros = request.form.get('kilometros')
        puertas = request.form.get('puertas')
        plazas = request.form.get('plazas')
        tipo = request.form.get('tipo')

        coche_id = ModelUser.agregar_coche(
            db, marca, modelo, anio, precio_contado, precio_financiado, estado,
            descripcion, motor, consumo, cambio,
            combustible, kilometros, puertas, plazas, tipo
        )

        if not coche_id:
            flash("Error al insertar el coche", "danger")
            return redirect(url_for('panel'))

        carpeta_final = os.path.join(DISCO_RENDER, "uploads", str(coche_id))
        os.makedirs(carpeta_final, exist_ok=True)
        cursor = db.connection.cursor()

        fotos = request.files.getlist('fotos[]')
        for foto in fotos:
            if foto and foto.filename != '':
                filename = secure_filename(foto.filename)
                ruta_destino = os.path.join(carpeta_final, filename)

                try:
                    foto.save(ruta_destino)
                except Exception as e:
                    print(f"Error guardando imagen: {e}")

                ruta_relativa = os.path.join(str(coche_id), filename).replace('\\', '/')
                cursor.execute("INSERT INTO fotos (coche_id, ruta) VALUES (%s, %s)", (coche_id, ruta_relativa))


        db.connection.commit()

        flash("Coche e imágenes insertados correctamente", "success")
        return redirect(url_for('panel'))


@app.route('/vehiculos', methods=["POST", "GET"])
def ver_vehiculos():
    if not current_user.is_authenticated:
        return redirect("/")
    else:
        cur = db.connection.cursor()

        # Obtener todos los coches
        cur.execute("SELECT * FROM coches")
        coches = cur.fetchall()

        # Obtener todas las fotos
        cur.execute("SELECT coche_id , ruta FROM fotos")
        fotos = cur.fetchall()
        cur.close()

        # Agrupar fotos por id_coche
        fotos_por_coche = {}
        for foto in fotos:
            id_coche = foto[0]
            ruta = foto[1].replace("\\", "/")  # corregimos las barras
            if id_coche not in fotos_por_coche:
                fotos_por_coche[id_coche] = []
            fotos_por_coche[id_coche].append(ruta)
            

            # Convertir lista de tuplas a lista de listas + añadir fotos
        coches_con_fotos = []
        for coche in coches:
            id_coche = coche[0]
            fotos = fotos_por_coche.get(id_coche, [])
            coches_con_fotos.append((coche, fotos))
        print(coches_con_fotos)

        return render_template('vehiculos.html', coches=coches_con_fotos)

@app.route("/eliminar_vehiculo/<int:id>" , methods=["POST", "GET"])
def eliminar_vehiculo(id):
    if not current_user.is_authenticated:
        return redirect("/")
    else:
        # Eliminar el coche de la base de datos
        ModelUser.eliminar_coche(db, id)

        # Eliminar la carpeta del coche
        carpeta_vehiculo = os.path.join("static/uploads", str(id))
        if os.path.exists(carpeta_vehiculo):
            shutil.rmtree(carpeta_vehiculo)

        flash("Vehículo eliminado con éxito", "success")
        return redirect(url_for("ver_vehiculos"))

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html"), 404

@app.route("/cerrar_sesion", methods=["GET"])
def logout():
    logout_user()
    flash("sesion cerrada con exito", "success")
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run()
