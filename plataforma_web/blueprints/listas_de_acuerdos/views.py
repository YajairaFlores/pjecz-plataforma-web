"""
Listas de Acuerdos, vistas
"""
import datetime
import json
from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from google.cloud import storage
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import secure_filename

from lib import datatables
from lib.safe_string import safe_message, safe_string
from lib.time_to_text import dia_mes_ano, mes_en_palabra
from plataforma_web.blueprints.usuarios.decorators import permission_required

from plataforma_web.blueprints.autoridades.models import Autoridad
from plataforma_web.blueprints.bitacoras.models import Bitacora
from plataforma_web.blueprints.distritos.models import Distrito
from plataforma_web.blueprints.listas_de_acuerdos.forms import ListaDeAcuerdoNewForm, ListaDeAcuerdoEditForm, ListaDeAcuerdoSearchForm, ListaDeAcuerdoSearchAdminForm
from plataforma_web.blueprints.listas_de_acuerdos.models import ListaDeAcuerdo
from plataforma_web.blueprints.listas_de_acuerdos_acuerdos.models import ListaDeAcuerdoAcuerdo
from plataforma_web.blueprints.modulos.models import Modulo
from plataforma_web.blueprints.permisos.models import Permiso

listas_de_acuerdos = Blueprint("listas_de_acuerdos", __name__, template_folder="templates")

MODULO = "LISTAS DE ACUERDOS"
SUBDIRECTORIO = "Listas de Acuerdos"
LIMITE_DIAS = 30  # Es el máximo, aunque autoridad.limite_dias_listas_de_acuerdos sea mayor, gana el menor
LIMITE_ADMINISTRADORES_DIAS = 90


@listas_de_acuerdos.route("/listas_de_acuerdos/acuses/<id_hashed>")
def checkout(id_hashed):
    """Acuse"""
    lista_de_acuerdo = ListaDeAcuerdo.query.get_or_404(ListaDeAcuerdo.decode_id(id_hashed))
    dia, mes, ano = dia_mes_ano(lista_de_acuerdo.creado)
    return render_template("listas_de_acuerdos/checkout.jinja2", lista_de_acuerdo=lista_de_acuerdo, dia=dia, mes=mes.upper(), ano=ano)


@listas_de_acuerdos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@listas_de_acuerdos.route("/listas_de_acuerdos")
def list_active():
    """Listado de Listas de Acuerdos activas"""
    # Si es administrador ve todo
    if current_user.can_admin("LISTAS DE ACUERDOS"):
        return render_template(
            "listas_de_acuerdos/list_admin.jinja2",
            autoridad=None,
            filtros=json.dumps({"estatus": "A"}),
            titulo="Todas las Listas de Acuerdo",
            estatus="A",
        )
    # Si es jurisdiccional ve lo de su autoridad
    if current_user.autoridad.es_jurisdiccional:
        autoridad = current_user.autoridad
        return render_template(
            "listas_de_acuerdos/list.jinja2",
            autoridad=autoridad,
            filtros=json.dumps({"autoridad_id": autoridad.id, "estatus": "A"}),
            titulo=f"Listas de Acuerdos de {autoridad.distrito.nombre_corto}, {autoridad.descripcion_corta}",
            estatus="A",
        )
    # Ninguno de los anteriores
    return redirect(url_for("listas_de_acuerdos.list_distritos"))


@listas_de_acuerdos.route("/listas_de_acuerdos/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Listas de Acuerdos inactivas"""
    # Si es administrador ve todo
    if current_user.can_admin("LISTAS DE ACUERDOS"):
        return render_template(
            "listas_de_acuerdos/list_admin.jinja2",
            autoridad=None,
            filtros=json.dumps({"estatus": "B"}),
            titulo="Todas las Listas de Acuerdos inactivas",
            estatus="B",
        )
    # Si es jurisdiccional ve lo de su autoridad
    if current_user.autoridad.es_jurisdiccional:
        autoridad = current_user.autoridad
        return render_template(
            "listas_de_acuerdos/list.jinja2",
            autoridad=autoridad,
            filtros=json.dumps({"autoridad_id": autoridad.id, "estatus": "B"}),
            titulo=f"Listas de Acuerdos inactivas de {autoridad.distrito.nombre_corto}, {autoridad.descripcion_corta}",
            estatus="B",
        )
    # Ninguno de los anteriores
    return redirect(url_for("listas_de_acuerdos.list_distritos"))


@listas_de_acuerdos.route("/listas_de_acuerdos/distritos")
def list_distritos():
    """Listado de Distritos"""
    return render_template(
        "listas_de_acuerdos/list_distritos.jinja2",
        distritos=Distrito.query.filter_by(es_distrito_judicial=True).filter_by(estatus="A").order_by(Distrito.nombre).all(),
    )


@listas_de_acuerdos.route("/listas_de_acuerdos/distrito/<int:distrito_id>")
def list_autoridades(distrito_id):
    """Listado de Autoridades de un distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    return render_template(
        "listas_de_acuerdos/list_autoridades.jinja2",
        distrito=distrito,
        autoridades=Autoridad.query.filter(Autoridad.distrito == distrito).filter_by(es_jurisdiccional=True).filter_by(es_notaria=False).filter_by(estatus="A").order_by(Autoridad.clave).all(),
    )


@listas_de_acuerdos.route("/listas_de_acuerdos/autoridad/<int:autoridad_id>")
def list_autoridad_listas_de_acuerdos(autoridad_id):
    """Listado de Listas de Acuerdos activas de una autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if current_user.can_admin("LISTAS DE ACUERDOS"):
        plantilla = "listas_de_acuerdos/list_admin.jinja2"
    else:
        plantilla = "listas_de_acuerdos/list.jinja2"
    return render_template(
        plantilla,
        autoridad=autoridad,
        filtros=json.dumps({"autoridad_id": autoridad.id, "estatus": "A"}),
        titulo=f"Listas de Acuerdos de {autoridad.distrito.nombre_corto}, {autoridad.descripcion_corta}",
        estatus="A",
    )


@listas_de_acuerdos.route("/listas_de_acuerdos/inactivos/autoridad/<int:autoridad_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_autoridad_listas_de_acuerdos_inactive(autoridad_id):
    """Listado de Listas de Acuerdos inactivas de una autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if current_user.can_admin("LISTAS DE ACUERDOS"):
        plantilla = "listas_de_acuerdos/list_admin.jinja2"
    else:
        plantilla = "listas_de_acuerdos/list.jinja2"
    return render_template(
        plantilla,
        autoridad=autoridad,
        filtros=json.dumps({"autoridad_id": autoridad.id, "estatus": "B"}),
        titulo=f"Listas de Acuerdos inactivas de {autoridad.distrito.nombre_corto}, {autoridad.descripcion_corta}",
        estatus="B",
    )


@listas_de_acuerdos.route("/listas_de_acuerdos/buscar", methods=["GET", "POST"])
def search():
    """Buscar Lista de Acuerdos"""
    if current_user.can_admin("LISTAS DE ACUERDOS"):
        puede_elegir_autoridad = True
    elif current_user.autoridad.es_jurisdiccional:
        puede_elegir_autoridad = False
    else:
        puede_elegir_autoridad = True
    if puede_elegir_autoridad:
        form_search = ListaDeAcuerdoSearchAdminForm()
    else:
        form_search = ListaDeAcuerdoSearchForm()
    if form_search.validate_on_submit():
        busqueda = {"estatus": "A"}
        titulos = []
        fallo_validacion = False
        # Autoridad es un campo obligatorio
        if puede_elegir_autoridad:
            autoridad = Autoridad.query.get(form_search.autoridad.data)
            plantilla = "listas_de_acuerdos/list_admin.jinja2"
        else:
            autoridad = current_user.autoridad
            plantilla = "listas_de_acuerdos/list.jinja2"
        busqueda["autoridad_id"] = autoridad.id
        titulos.append(autoridad.distrito.nombre_corto + ", " + autoridad.descripcion_corta)
        # Fecha
        if form_search.fecha_desde.data:
            busqueda["fecha_desde"] = form_search.fecha_desde.data.strftime("%Y-%m-%d")
            titulos.append("desde " + busqueda["fecha_desde"])
        if form_search.fecha_hasta.data:
            busqueda["fecha_hasta"] = form_search.fecha_hasta.data.strftime("%Y-%m-%d")
            titulos.append("hasta " + busqueda["fecha_hasta"])
        # Mostrar resultados
        if not fallo_validacion:
            return render_template(
                plantilla,
                filtros=json.dumps(busqueda),
                titulo="Listas de Acuerdos con " + ", ".join(titulos),
            )
    # Mostrar buscador donde puede elegir la autoridad
    if puede_elegir_autoridad:
        return render_template(
            "listas_de_acuerdos/search_admin.jinja2",
            form=form_search,
            distritos=Distrito.query.filter_by(es_distrito_judicial=True).filter_by(estatus="A").order_by(Distrito.nombre).all(),
            autoridades=Autoridad.query.filter_by(es_jurisdiccional=True).filter_by(es_notaria=False).filter_by(estatus="A").order_by(Autoridad.clave).all(),
        )
    # Mostrar buscador con la autoridad fija
    form_search.distrito.data = current_user.autoridad.distrito.nombre
    form_search.autoridad.data = current_user.autoridad.descripcion
    return render_template("listas_de_acuerdos/search.jinja2", form=form_search)


@listas_de_acuerdos.route("/listas_de_acuerdos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de listas de acuerdos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = datatables.get_parameters()
    # Consultar
    consulta = ListaDeAcuerdo.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "autoridad_id" in request.form:
        autoridad = Autoridad.query.get(request.form["autoridad_id"])
        if autoridad:
            consulta = consulta.filter_by(autoridad=autoridad)
    if "fecha_desde" in request.form:
        consulta = consulta.filter(ListaDeAcuerdo.fecha >= request.form["fecha_desde"])
    if "fecha_hasta" in request.form:
        consulta = consulta.filter(ListaDeAcuerdo.fecha <= request.form["fecha_hasta"])
    registros = consulta.order_by(ListaDeAcuerdo.fecha.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for lista_de_acuerdo in registros:
        data.append(
            {
                "fecha": lista_de_acuerdo.fecha.strftime("%Y-%m-%d"),
                "detalle": {
                    "descripcion": lista_de_acuerdo.descripcion,
                    "url": url_for("listas_de_acuerdos.detail", lista_de_acuerdo_id=lista_de_acuerdo.id),
                },
                "archivo": {
                    "url": lista_de_acuerdo.url,
                },
            }
        )
    # Entregar JSON
    return datatables.output(draw, total, data)


@listas_de_acuerdos.route("/listas_de_acuerdos/datatable_json_admin", methods=["GET", "POST"])
def datatable_json_admin():
    """DataTable JSON para listado de listas de acuerdos admin"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = datatables.get_parameters()
    # Consultar
    consulta = ListaDeAcuerdo.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "autoridad_id" in request.form:
        autoridad = Autoridad.query.get(request.form["autoridad_id"])
        if autoridad:
            consulta = consulta.filter_by(autoridad=autoridad)
    if "fecha_desde" in request.form:
        consulta = consulta.filter(ListaDeAcuerdo.fecha >= request.form["fecha_desde"])
    if "fecha_hasta" in request.form:
        consulta = consulta.filter(ListaDeAcuerdo.fecha <= request.form["fecha_hasta"])
    registros = consulta.order_by(ListaDeAcuerdo.fecha.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for lista_de_acuerdo in registros:
        data.append(
            {
                "creado": lista_de_acuerdo.creado.strftime("%Y-%m-%d %H:%M:%S"),
                "autoridad": lista_de_acuerdo.autoridad.clave,
                "fecha": lista_de_acuerdo.fecha.strftime("%Y-%m-%d"),
                "detalle": {
                    "descripcion": lista_de_acuerdo.descripcion,
                    "url": url_for("listas_de_acuerdos.detail", lista_de_acuerdo_id=lista_de_acuerdo.id),
                },
                "archivo": {
                    "url": lista_de_acuerdo.url,
                },
            }
        )
    # Entregar JSON
    return datatables.output(draw, total, data)


@listas_de_acuerdos.route("/listas_de_acuerdos/refrescar/<int:autoridad_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def refresh(autoridad_id):
    """Refrescar Listas de Acuerdos"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if current_user.get_task_in_progress("listas_de_acuerdos.tasks.refrescar"):
        flash("Debe esperar porque hay una tarea en el fondo sin terminar.", "warning")
    else:
        tarea = current_user.launch_task(
            nombre="listas_de_acuerdos.tasks.refrescar",
            descripcion=f"Refrescar listas de acuerdos de {autoridad.clave}",
            usuario_id=current_user.id,
            autoridad_id=autoridad.id,
        )
        flash(f"{tarea.descripcion} está corriendo en el fondo.", "info")
    return redirect(url_for("listas_de_acuerdos.list_autoridad_listas_de_acuerdos", autoridad_id=autoridad.id))


@listas_de_acuerdos.route("/listas_de_acuerdos/<int:lista_de_acuerdo_id>")
def detail(lista_de_acuerdo_id):
    """Detalle de una Lista de Acuerdos"""
    lista_de_acuerdo = ListaDeAcuerdo.query.get_or_404(lista_de_acuerdo_id)
    acuerdos = None  # Por lo pronto sólo los administradores ven los acuerdos
    if current_user.can_admin("LISTAS DE ACUERDOS"):
        acuerdos = ListaDeAcuerdoAcuerdo.query.filter(ListaDeAcuerdoAcuerdo.lista_de_acuerdo == lista_de_acuerdo).filter_by(estatus="A").all()
    return render_template("listas_de_acuerdos/detail.jinja2", lista_de_acuerdo=lista_de_acuerdo, acuerdos=acuerdos)


def new_success(lista_de_acuerdo, anterior_borrada):
    """Mensaje de éxito en nueva lista de acuerdos"""
    if anterior_borrada:
        mensaje = "Reemplazada "
    else:
        mensaje = "Nueva "
    mensaje = mensaje + f"lista de acuerdos del {lista_de_acuerdo.fecha.strftime('%Y-%m-%d')} de {lista_de_acuerdo.autoridad.clave}"
    bitacora = Bitacora(
        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
        usuario=current_user,
        descripcion=safe_message(mensaje),
        url=url_for("listas_de_acuerdos.detail", lista_de_acuerdo_id=lista_de_acuerdo.id),
    )
    bitacora.save()
    return bitacora


@listas_de_acuerdos.route("/listas_de_acuerdos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Subir Lista de Acuerdos como juzgado"""

    # Validar autoridad
    autoridad = current_user.autoridad
    if autoridad is None or autoridad.estatus != "A":
        flash("El juzgado/autoridad no existe o no es activa.", "warning")
        return redirect(url_for("listas_de_acuerdos.list_active"))
    if not autoridad.distrito.es_distrito_judicial:
        flash("El juzgado/autoridad no está en un distrito jurisdiccional.", "warning")
        return redirect(url_for("listas_de_acuerdos.list_active"))
    if not autoridad.es_jurisdiccional:
        flash("El juzgado/autoridad no es jurisdiccional.", "warning")
        return redirect(url_for("listas_de_acuerdos.list_active"))
    if autoridad.directorio_listas_de_acuerdos is None or autoridad.directorio_listas_de_acuerdos == "":
        flash("El juzgado/autoridad no tiene directorio para listas de acuerdos.", "warning")
        return redirect(url_for("listas_de_acuerdos.list_active"))

    # Para validar la fecha
    hoy = datetime.date.today()
    hoy_dt = datetime.datetime(year=hoy.year, month=hoy.month, day=hoy.day)
    if autoridad.limite_dias_listas_de_acuerdos < LIMITE_DIAS:
        mi_limite_dias = autoridad.limite_dias_listas_de_acuerdos
    else:
        mi_limite_dias = LIMITE_DIAS
    if mi_limite_dias > 0:
        limite_dt = hoy_dt + datetime.timedelta(days=-mi_limite_dias)
    else:
        limite_dt = hoy_dt

    # Si viene el formulario
    form = ListaDeAcuerdoNewForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():

        # Tomar valores del formulario
        fecha = form.fecha.data
        descripcion = safe_string(form.descripcion.data)
        archivo = request.files["archivo"]

        # Validar fecha
        if not limite_dt <= datetime.datetime(year=fecha.year, month=fecha.month, day=fecha.day) <= hoy_dt:
            flash(f"La fecha no debe ser del futuro ni anterior a {mi_limite_dias} días.", "warning")
            form.fecha.data = hoy
            return render_template("listas_de_acuerdos/new.jinja2", form=form, mi_limite_dias=mi_limite_dias)

        # Validar descripcion, porque safe_string puede resultar vacío
        if descripcion == "":
            flash("La descripción es incorrecta.", "warning")
            return render_template("listas_de_acuerdos/new.jinja2", form=form, mi_limite_dias=mi_limite_dias)

        # Validar archivo
        archivo_nombre = secure_filename(archivo.filename.lower())
        if "." not in archivo_nombre or archivo_nombre.rsplit(".", 1)[1] != "pdf":
            flash("No es un archivo PDF.", "warning")
            return render_template("listas_de_acuerdos/new.jinja2", form=form, mi_limite_dias=mi_limite_dias)

        # Si existe una lista de acuerdos de la misma fecha, dar de baja la antigua
        anterior_borrada = False
        anterior_lista_de_acuerdo = ListaDeAcuerdo.query.filter(ListaDeAcuerdo.autoridad == autoridad).filter(ListaDeAcuerdo.fecha == fecha).filter_by(estatus="A").first()
        if anterior_lista_de_acuerdo:
            anterior_lista_de_acuerdo.delete()
            anterior_borrada = True

        # Insertar registro
        lista_de_acuerdo = ListaDeAcuerdo(
            autoridad=autoridad,
            fecha=fecha,
            descripcion=descripcion,
        )
        lista_de_acuerdo.save()

        # Elaborar nombre del archivo y ruta SUBDIRECTORIO/Autoridad/YYYY/MES/archivo.pdf
        ano_str = fecha.strftime("%Y")
        mes_str = mes_en_palabra(fecha.month)
        fecha_str = fecha.strftime("%Y-%m-%d")
        descripcion_str = descripcion.replace(" ", "-")
        archivo_str = f"{fecha_str}-{descripcion_str}-{lista_de_acuerdo.encode_id()}.pdf"
        ruta_str = str(Path(SUBDIRECTORIO, autoridad.directorio_listas_de_acuerdos, ano_str, mes_str, archivo_str))

        # Subir el archivo
        deposito = current_app.config["CLOUD_STORAGE_DEPOSITO"]
        storage_client = storage.Client()
        bucket = storage_client.bucket(deposito)
        blob = bucket.blob(ruta_str)
        blob.upload_from_string(archivo.stream.read(), content_type="application/pdf")
        url = blob.public_url

        # Actualizar el nombre del archivo y el url
        lista_de_acuerdo.archivo = archivo_str
        lista_de_acuerdo.url = url
        lista_de_acuerdo.save()

        # Mostrar mensaje de éxito e ir al detalle
        bitacora = new_success(lista_de_acuerdo, anterior_borrada)
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)

    # Prellenado de los campos
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    form.descripcion.data = "LISTA DE ACUERDOS"
    form.fecha.data = hoy
    return render_template("listas_de_acuerdos/new.jinja2", form=form, mi_limite_dias=mi_limite_dias)


@listas_de_acuerdos.route("/listas_de_acuerdos/nuevo/<int:autoridad_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.ADMINISTRAR)
def new_for_autoridad(autoridad_id):
    """Subir Lista de Acuerdos para una autoridad dada"""

    # Validar autoridad
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if autoridad is None:
        flash("El juzgado/autoridad no existe.", "warning")
        return redirect(url_for("listas_de_acuerdos.list_active"))
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))
    if not autoridad.distrito.es_distrito_judicial:
        flash("El juzgado/autoridad no está en un distrito jurisdiccional.", "warning")
        return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))
    if not autoridad.es_jurisdiccional:
        flash("El juzgado/autoridad no es jurisdiccional.", "warning")
        return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))
    if autoridad.directorio_listas_de_acuerdos is None or autoridad.directorio_listas_de_acuerdos == "":
        flash("El juzgado/autoridad no tiene directorio para edictos.", "warning")
        return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))

    # Para validar la fecha
    hoy = datetime.date.today()
    hoy_dt = datetime.datetime(year=hoy.year, month=hoy.month, day=hoy.day)
    limite_dt = hoy_dt + datetime.timedelta(days=-LIMITE_ADMINISTRADORES_DIAS)

    # Si viene el formulario
    form = ListaDeAcuerdoNewForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():

        # Tomar valores del formulario
        fecha = form.fecha.data
        descripcion = safe_string(form.descripcion.data)
        archivo = request.files["archivo"]

        # Validar fecha
        archivo_nombre = secure_filename(archivo.filename.lower())
        if not limite_dt <= datetime.datetime(year=fecha.year, month=fecha.month, day=fecha.day) <= hoy_dt:
            flash(f"La fecha no debe ser del futuro ni anterior a {LIMITE_ADMINISTRADORES_DIAS} días.", "warning")
            form.fecha.data = hoy
            return render_template("listas_de_acuerdos/new_for_autoridad.jinja2", form=form, autoridad=autoridad)

        # Validar descripcion, porque safe_string puede resultar vacío
        if descripcion == "":
            flash("La descripción es incorrecta.", "warning")
            return render_template("listas_de_acuerdos/new_for_autoridad.jinja2", form=form, autoridad=autoridad)

        # Validar archivo
        if "." not in archivo_nombre or archivo_nombre.rsplit(".", 1)[1] != "pdf":
            flash("No es un archivo PDF.", "warning")
            return render_template("listas_de_acuerdos/new_for_autoridad.jinja2", form=form, autoridad=autoridad)

        # Si existe una lista de acuerdos de la misma fecha, dar de baja la antigua
        anterior_borrada = False
        anterior_lista_de_acuerdo = ListaDeAcuerdo.query.filter(ListaDeAcuerdo.autoridad == autoridad).filter(ListaDeAcuerdo.fecha == fecha).filter_by(estatus="A").first()
        if anterior_lista_de_acuerdo:
            anterior_lista_de_acuerdo.delete()
            anterior_borrada = True

        # Insertar registro
        lista_de_acuerdo = ListaDeAcuerdo(
            autoridad=autoridad,
            fecha=fecha,
            descripcion=descripcion,
        )
        lista_de_acuerdo.save()

        # Elaborar nombre del archivo
        ano_str = fecha.strftime("%Y")
        mes_str = mes_en_palabra(fecha.month)
        fecha_str = fecha.strftime("%Y-%m-%d")
        descripcion_str = descripcion.replace(" ", "-")
        archivo_str = f"{fecha_str}-{descripcion_str}-{lista_de_acuerdo.encode_id()}.pdf"
        ruta_str = str(Path(SUBDIRECTORIO, autoridad.directorio_listas_de_acuerdos, ano_str, mes_str, archivo_str))

        # Subir el archivo
        deposito = current_app.config["CLOUD_STORAGE_DEPOSITO"]
        storage_client = storage.Client()
        bucket = storage_client.bucket(deposito)
        blob = bucket.blob(ruta_str)
        blob.upload_from_string(archivo.stream.read(), content_type="application/pdf")
        url = blob.public_url

        # Actualizar el nombre del archivo y el url
        lista_de_acuerdo.archivo = archivo_str
        lista_de_acuerdo.url = url
        lista_de_acuerdo.save()

        # Mostrar mensaje de éxito e ir al detalle
        bitacora = new_success(lista_de_acuerdo, anterior_borrada)
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)

    # Prellenado de los campos
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    form.descripcion.data = "LISTA DE ACUERDOS"
    form.fecha.data = hoy
    return render_template("listas_de_acuerdos/new_for_autoridad.jinja2", form=form, autoridad=autoridad)


@listas_de_acuerdos.route("/listas_de_acuerdos/edicion/<int:lista_de_acuerdo_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.ADMINISTRAR)
def edit(lista_de_acuerdo_id):
    """Editar Lista de Acuerdos"""
    lista_de_acuerdo = ListaDeAcuerdo.query.get_or_404(lista_de_acuerdo_id)
    form = ListaDeAcuerdoEditForm()
    if form.validate_on_submit():
        lista_de_acuerdo.fecha = form.fecha.data
        lista_de_acuerdo.descripcion = safe_string(form.descripcion.data)
        lista_de_acuerdo.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editada la lista de acuerdos del {lista_de_acuerdo.fecha.strftime('%Y-%m-%d')} de {lista_de_acuerdo.autoridad.clave}"),
            url=url_for("listas_de_acuerdos.detail", lista_de_acuerdo_id=lista_de_acuerdo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.fecha.data = lista_de_acuerdo.fecha
    form.descripcion.data = lista_de_acuerdo.descripcion
    return render_template("listas_de_acuerdos/edit.jinja2", form=form, lista_de_acuerdo=lista_de_acuerdo)


def delete_success(lista_de_acuerdo):
    """Mensaje de éxito al eliminar una lista de acuerdos"""
    bitacora = Bitacora(
        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
        usuario=current_user,
        descripcion=safe_message(f"Eliminada la lista de acuerdos del {lista_de_acuerdo.fecha.strftime('%Y-%m-%d')} de {lista_de_acuerdo.autoridad.clave}"),
        url=url_for("listas_de_acuerdos.detail", lista_de_acuerdo_id=lista_de_acuerdo.id),
    )
    bitacora.save()
    return bitacora


@listas_de_acuerdos.route("/listas_de_acuerdos/eliminar/<int:lista_de_acuerdo_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(lista_de_acuerdo_id):
    """Eliminar Lista de Acuerdos"""
    lista_de_acuerdo = ListaDeAcuerdo.query.get_or_404(lista_de_acuerdo_id)
    if lista_de_acuerdo.estatus == "A":
        if current_user.can_admin("LISTAS DE ACUERDOS"):
            hoy = datetime.date.today()
            hoy_dt = datetime.datetime(year=hoy.year, month=hoy.month, day=hoy.day)
            limite_dt = hoy_dt + datetime.timedelta(days=-LIMITE_ADMINISTRADORES_DIAS)
            if limite_dt.timestamp() <= lista_de_acuerdo.creado.timestamp():
                lista_de_acuerdo.delete()
                bitacora = delete_success(lista_de_acuerdo)
                flash(bitacora.descripcion, "success")
            else:
                flash(f"No tiene permiso para eliminar si fue creado hace {LIMITE_ADMINISTRADORES_DIAS} días o más.", "warning")
        elif current_user.autoridad_id == lista_de_acuerdo.autoridad_id and lista_de_acuerdo.fecha == datetime.date.today():
            lista_de_acuerdo.delete()
            bitacora = delete_success(lista_de_acuerdo)
            flash(bitacora.descripcion, "success")
        else:
            flash("No tiene permiso para eliminar o sólo puede eliminar de hoy.", "warning")
    return redirect(url_for("listas_de_acuerdos.detail", lista_de_acuerdo_id=lista_de_acuerdo_id))


def recover_success(lista_de_acuerdo):
    """Mensaje de éxito al recuperar una lista de acuerdos"""
    bitacora = Bitacora(
        modulo=Modulo.query.filter_by(nombre=MODULO).first(),
        usuario=current_user,
        descripcion=safe_message(f"Recuperada la lista de acuerdos del {lista_de_acuerdo.fecha.strftime('%Y-%m-%d')} de {lista_de_acuerdo.autoridad.clave}"),
        url=url_for("listas_de_acuerdos.detail", lista_de_acuerdo_id=lista_de_acuerdo.id),
    )
    bitacora.save()
    return bitacora


@listas_de_acuerdos.route("/listas_de_acuerdos/recuperar/<int:lista_de_acuerdo_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(lista_de_acuerdo_id):
    """Recuperar Lista de Acuerdos"""
    lista_de_acuerdo = ListaDeAcuerdo.query.get_or_404(lista_de_acuerdo_id)
    if lista_de_acuerdo.estatus == "B":
        if ListaDeAcuerdo.query.filter(ListaDeAcuerdo.autoridad == current_user.autoridad).filter(ListaDeAcuerdo.fecha == lista_de_acuerdo.fecha).filter_by(estatus="A").first():
            flash("No puede recuperar esta lista porque ya hay una activa de la misma fecha.", "warning")
        else:
            if current_user.can_admin("LISTAS DE ACUERDOS"):
                hoy = datetime.date.today()
                hoy_dt = datetime.datetime(year=hoy.year, month=hoy.month, day=hoy.day)
                limite_dt = hoy_dt + datetime.timedelta(days=-LIMITE_ADMINISTRADORES_DIAS)
                if limite_dt.timestamp() <= lista_de_acuerdo.creado.timestamp():
                    lista_de_acuerdo.recover()
                    bitacora = recover_success(lista_de_acuerdo)
                    flash(bitacora.descripcion, "success")
                else:
                    flash(f"No tiene permiso para recuperar si fue creado hace {LIMITE_ADMINISTRADORES_DIAS} días o más.", "warning")
            elif current_user.autoridad_id == lista_de_acuerdo.autoridad_id and lista_de_acuerdo.fecha == datetime.date.today():
                lista_de_acuerdo.recover()
                bitacora = recover_success(lista_de_acuerdo)
                flash(bitacora.descripcion, "success")
            else:
                flash("No tiene permiso para recuperar o sólo puede recuperar de hoy.", "warning")
    return redirect(url_for("listas_de_acuerdos.detail", lista_de_acuerdo_id=lista_de_acuerdo_id))
