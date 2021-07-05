"""
Audiencias, vistas
"""
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from lib.safe_string import safe_message, safe_string

from plataforma_web.blueprints.roles.models import Permiso
from plataforma_web.blueprints.usuarios.decorators import permission_required

from plataforma_web.blueprints.autoridades.models import Autoridad
from plataforma_web.blueprints.bitacoras.models import Bitacora
from plataforma_web.blueprints.distritos.models import Distrito
from plataforma_web.blueprints.audiencias.models import Audiencia
from plataforma_web.blueprints.audiencias.forms import AudienciaGenericaForm, AudienciaMapoForm, AudienciaDipeForm, AudienciaSapeForm

audiencias = Blueprint("audiencias", __name__, template_folder="templates")

MODULO = "AUDIENCIAS"
LIMITE_CONSULTAS = 400


@audiencias.before_request
@login_required
@permission_required(Permiso.VER_JUSTICIABLES)
def before_request():
    """Permiso por defecto"""


@audiencias.route("/audiencias")
def list_active():
    """Listado de Audiencias activos"""
    # Si es administrador, ve las audiencias de todas las autoridades
    if current_user.can_admin("audiencias"):
        audiencias_activas = Audiencia.query.filter(Audiencia.estatus == "A").order_by(Audiencia.creado.desc()).limit(LIMITE_CONSULTAS).all()
        return render_template("audiencias/list_admin.jinja2", audiencias=audiencias_activas, estatus="A")
    # No es administrador, consultar su autoridad
    if current_user.autoridad.es_jurisdiccional:
        sus_audiencias_activas = Audiencia.query.filter(Audiencia.autoridad == current_user.autoridad).filter(Audiencia.estatus == "A").order_by(Audiencia.creado.desc()).limit(LIMITE_CONSULTAS).all()
        return render_template("audiencias/list.jinja2", autoridad=current_user.autoridad, audiencias=sus_audiencias_activas, estatus="A")
    # No es jurisdiccional, se redirige al listado de distritos
    return redirect(url_for("audiencias.list_distritos"))


@audiencias.route("/audiencias/inactivos")
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def list_inactive():
    """Listado de Audiencias inactivos"""
    # Si es administrador, ve las audiencias de todas las autoridades
    if current_user.can_admin("audiencias"):
        audiencias_inactivas = Audiencia.query.filter(Audiencia.estatus == "B").order_by(Audiencia.creado.desc()).limit(LIMITE_CONSULTAS).all()
        return render_template("audiencias/list_admin.jinja2", audiencias=audiencias_inactivas, estatus="B")
    # No es administrador, consultar su autoridad
    if current_user.autoridad.es_jurisdiccional:
        sus_audiencias_inactivas = Audiencia.query.filter(Audiencia.autoridad == current_user.autoridad).filter(Audiencia.estatus == "B").order_by(Audiencia.creado.desc()).limit(LIMITE_CONSULTAS).all()
        return render_template("audiencias/list.jinja2", autoridad=current_user.autoridad, audiencias=sus_audiencias_inactivas, estatus="B")
    # No es jurisdiccional, se redirige al listado de distritos
    return redirect(url_for("audiencias.list_distritos"))


@audiencias.route("/audiencias/distritos")
def list_distritos():
    """Listado de Distritos"""
    distritos = Distrito.query.filter(Distrito.es_distrito_judicial == True).filter(Distrito.estatus == "A").order_by(Distrito.nombre).all()
    return render_template("audiencias/list_distritos.jinja2", distritos=distritos)


@audiencias.route("/audiencias/distrito/<int:distrito_id>")
def list_autoridades(distrito_id):
    """Listado de Autoridades de un distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    autoridades = Autoridad.query.filter(Autoridad.distrito == distrito).filter(Autoridad.estatus == "A").order_by(Autoridad.clave).all()
    return render_template("audiencias/list_autoridades.jinja2", distrito=distrito, autoridades=autoridades)


@audiencias.route("/audiencias/autoridad/<int:autoridad_id>")
def list_autoridad_audiencias(autoridad_id):
    """Listado de Audiencias activas de una autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    audiencias_activas = Audiencia.query.filter(Audiencia.autoridad == autoridad).filter(Audiencia.estatus == "A").order_by(Audiencia.creado.desc()).limit(LIMITE_CONSULTAS).all()
    if current_user.can_admin("audiencias"):
        return render_template("audiencias/list_admin.jinja2", autoridad=autoridad, audiencias=audiencias_activas, estatus="A")
    return render_template("audiencias/list.jinja2", autoridad=autoridad, audiencias=audiencias_activas, estatus="A")


@audiencias.route("/audiencias/inactivos/autoridad/<int:autoridad_id>")
@permission_required(Permiso.ADMINISTRAR_JUSTICIABLES)
def list_autoridad_audiencias_inactive(autoridad_id):
    """Listado de Audiencias inactivas de una autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    audiencias_inactivas = Audiencia.query.filter(Audiencia.autoridad == autoridad).filter(Audiencia.estatus == "B").order_by(Audiencia.creado.desc()).limit(LIMITE_CONSULTAS).all()
    if current_user.can_admin("audiencias"):
        return render_template("audiencias/list_admin.jinja2", autoridad=autoridad, audiencias=audiencias_inactivas, estatus="B")
    return render_template("audiencias/list.jinja2", autoridad=autoridad, audiencias=audiencias_inactivas, estatus="B")


@audiencias.route("/audiencias/<int:audiencia_id>")
def detail(audiencia_id):
    """Detalle de una Audiencia"""
    audiencia = Audiencia.query.get_or_404(audiencia_id)
    return render_template("audiencias/detail.jinja2", audiencia=audiencia)


@audiencias.route("/audiencias/nuevo", methods=["GET", "POST"])
@permission_required(Permiso.CREAR_JUSTICIABLES)
def new():
    """Nueva Audiencia"""
    autoridad = current_user.autoridad
    if autoridad.estatus != "A":
        flash("Su juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria == "CIVIL FAMILIAR MERCANTIL LETRADO TCYA":
        return redirect(url_for("audiencias.new_generica"))
    if autoridad.audiencia_categoria == "MATERIA ACUSATORIO PENAL ORAL":
        return redirect(url_for("audiencias.new_mapo"))
    if autoridad.audiencia_categoria == "DISTRITALES":
        return redirect(url_for("audiencias.new_dipe"))
    if autoridad.audiencia_categoria == "SALAS":
        return redirect(url_for("audiencias.new_sape"))
    flash("El juzgado/autoridad no tiene una categoría de audiencias correcta.", "warning")
    return redirect(url_for("audiencias.list_active"))


@audiencias.route("/audiencias/nuevo/generica", methods=["GET", "POST"])
@permission_required(Permiso.CREAR_JUSTICIABLES)
def new_generica():
    """Nueva Audiencia Materias CIVIL FAMILIAR MERCANTIL LETRADO TCYA"""

    # Validar autoridad
    autoridad = current_user.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria != "CIVIL FAMILIAR MERCANTIL LETRADO TCYA":
        flash("La categoría de audiencia no es CIVIL FAMILIAR MERCANTIL LETRADO TCYA.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Si viene el formulario
    form = AudienciaGenericaForm()
    if form.validate_on_submit():

        # Definir tiempo con la fecha y horas:minutos
        try:
            tiempo = datetime.combine(form.tiempo_fecha.data, form.tiempo_horas_minutos.data)
        except ValueError:
            flash("Error al definir el tiempo con la fecha y horas:minutos.", "warning")
            return redirect(url_for("audiencias.list_active"))

        # Insertar registro
        audiencia = Audiencia(
            autoridad=autoridad,
            tiempo=tiempo,
            tipo_audiencia=safe_string(form.tipo_audiencia.data),
            expediente=safe_string(form.expediente.data),
            actores=safe_string(form.actores.data),
            demandados=safe_string(form.demandados.data),
        )
        audiencia.save()

        # Mostrar mensaje de éxito e ir al detalle
        bitacora = Bitacora(
            modulo=MODULO,
            usuario=current_user,
            descripcion=safe_message("Nueva audiencia para " + audiencia.tiempo.strftime('%Y-%m-%d %H:%M')),
            url=url_for('audiencias.detail', audiencia_id=audiencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, 'success')
        return redirect(bitacora.url)

    # Prellenado del formulario
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    return render_template("audiencias/new_generica.jinja2", form=form)


@audiencias.route("/audiencias/nuevo/mapo", methods=["GET", "POST"])
@permission_required(Permiso.CREAR_JUSTICIABLES)
def new_mapo():
    """Nueva Audiencia MATERIA ACUSATORIO PENAL ORAL"""

    # Validar autoridad
    autoridad = current_user.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria != "MATERIA ACUSATORIO PENAL ORAL":
        flash("La categoría de audiencia no es MATERIA ACUSATORIO PENAL ORAL.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Si viene el formulario
    form = AudienciaMapoForm()
    if form.validate_on_submit():

        # Definir tiempo con la fecha y horas:minutos
        try:
            tiempo = datetime.combine(form.tiempo_fecha.data, form.tiempo_horas_minutos.data)
        except ValueError:
            flash("Error al definir el tiempo con la fecha y horas:minutos.", "warning")
            return redirect(url_for("audiencias.list_active"))

        # Insertar registro
        audiencia = Audiencia(
            autoridad=autoridad,
            tiempo=tiempo,
            tipo_audiencia=safe_string(form.tipo_audiencia.data),
            sala=safe_string(form.sala.data),
            caracter=safe_string(form.caracter.data),
            causa_penal=safe_string(form.causa_penal.data),
            delitos=safe_string(form.delitos.data),
        )
        audiencia.save()

        # Mostrar mensaje de éxito e ir al detalle
        bitacora = Bitacora(
            modulo=MODULO,
            usuario=current_user,
            descripcion=safe_message("Nueva audiencia para " + audiencia.tiempo.strftime('%Y-%m-%d %H:%M')),
            url=url_for('audiencias.detail', audiencia_id=audiencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, 'success')
        return redirect(bitacora.url)

    # Prellenado del formulario
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    return render_template("audiencias/new_mapo.jinja2", form=form)


@audiencias.route("/audiencias/nuevo/dipe", methods=["GET", "POST"])
@permission_required(Permiso.CREAR_JUSTICIABLES)
def new_dipe():
    """Nueva Audiencia DISTRITALES"""

    # Validar autoridad
    autoridad = current_user.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria != "DISTRITALES":
        flash("La categoría de audiencia no es DISTRITALES.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Si viene el formulario
    form = AudienciaDipeForm()
    if form.validate_on_submit():

        # Definir tiempo con la fecha y horas:minutos
        try:
            tiempo = datetime.combine(form.tiempo_fecha.data, form.tiempo_horas_minutos.data)
        except ValueError:
            flash("Error al definir el tiempo con la fecha y horas:minutos.", "warning")
            return redirect(url_for("audiencias.list_active"))

        # Insertar registro
        audiencia = Audiencia(
            autoridad=autoridad,
            tiempo=tiempo,
            tipo_audiencia=safe_string(form.tipo_audiencia.data),
            expediente=safe_string(form.expediente.data),
            actores=safe_string(form.actores.data),
            demandados=safe_string(form.demandados.data),
            toca=safe_string(form.toca.data),
            expediente_origen=safe_string(form.expediente_origen.data),
            imputados=safe_string(form.imputados.data),
        )
        audiencia.save()

        # Mostrar mensaje de éxito e ir al detalle
        bitacora = Bitacora(
            modulo=MODULO,
            usuario=current_user,
            descripcion=safe_message("Nueva audiencia para " + audiencia.tiempo.strftime('%Y-%m-%d %H:%M')),
            url=url_for('audiencias.detail', audiencia_id=audiencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, 'success')
        return redirect(bitacora.url)

    # Prellenado del formulario
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    return render_template("audiencias/new_dipe.jinja2", form=form)


@audiencias.route("/audiencias/nuevo/sape", methods=["GET", "POST"])
@permission_required(Permiso.CREAR_JUSTICIABLES)
def new_sape():
    """Nueva Audiencia SALAS"""

    # Validar autoridad
    autoridad = current_user.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria != "SALAS":
        flash("La categoría de audiencia no es SALAS.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Si viene el formulario
    form = AudienciaSapeForm()
    if form.validate_on_submit():

        # Definir tiempo con la fecha y horas:minutos
        try:
            tiempo = datetime.combine(form.tiempo_fecha.data, form.tiempo_horas_minutos.data)
        except ValueError:
            flash("Error al definir el tiempo con la fecha y horas:minutos.", "warning")
            return redirect(url_for("audiencias.list_active"))

        # Insertar registro
        audiencia = Audiencia(
            autoridad=autoridad,
            tiempo=tiempo,
            tipo_audiencia=safe_string(form.tipo_audiencia.data),
            expediente=safe_string(form.expediente.data),
            actores=safe_string(form.actores.data),
            demandados=safe_string(form.demandados.data),
            toca=safe_string(form.toca.data),
            expediente_origen=safe_string(form.expediente_origen.data),
            delitos=safe_string(form.delitos.data),
            origen=safe_string(form.origen.data),
        )
        audiencia.save()

        # Mostrar mensaje de éxito e ir al detalle
        bitacora = Bitacora(
            modulo=MODULO,
            usuario=current_user,
            descripcion=safe_message("Nueva audiencia para " + audiencia.tiempo.strftime('%Y-%m-%d %H:%M')),
            url=url_for('audiencias.detail', audiencia_id=audiencia.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, 'success')
        return redirect(bitacora.url)

    # Prellenado del formulario
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    return render_template("audiencias/new_sape.jinja2", form=form)


def edit_success(audiencia):
    """Mensaje de éxito al editar una audiencia"""
    bitacora = Bitacora(
        modulo=MODULO,
        usuario=current_user,
        descripcion=safe_message("Editada la audiencia del " + audiencia.tiempo.strftime('%Y-%m-%d %H:%M')),
        url=url_for('audiencias.detail', audiencia_id=audiencia.id),
    )
    bitacora.save()
    return bitacora


@audiencias.route('/audiencias/edicion/<int:audiencia_id>', methods=['GET', 'POST'])
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def edit(audiencia_id):
    """Editar Audiencia"""

    # Validad autoridad
    audiencia = Audiencia.query.get_or_404(audiencia_id)
    autoridad = audiencia.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Redirigir
    if autoridad.audiencia_categoria == "CIVIL FAMILIAR MERCANTIL LETRADO TCYA":
        return redirect(url_for("audiencias.edit_generica", audiencia_id=audiencia_id))
    if autoridad.audiencia_categoria == "MATERIA ACUSATORIO PENAL ORAL":
        return redirect(url_for("audiencias.edit_mapo", audiencia_id=audiencia_id))
    if autoridad.audiencia_categoria == "DISTRITALES":
        return redirect(url_for("audiencias.edit_dipes", audiencia_id=audiencia_id))
    if autoridad.audiencia_categoria == "SALAS":
        return redirect(url_for("audiencias.edit_sape", audiencia_id=audiencia_id))

    # Mensaje por no reconocer la categoría de audiencias
    flash("El juzgado/autoridad no tiene una categoría de audiencias correcta.", "warning")
    return redirect(url_for("audiencias.list_active"))


@audiencias.route('/audiencias/edicion/generica/<int:audiencia_id>', methods=['GET', 'POST'])
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def edit_generica(audiencia_id):
    """Editar Audiencia CIVIL FAMILIAR MERCANTIL LETRADO TCYA"""

    # Validar audiencia
    audiencia = Audiencia.query.get_or_404(audiencia_id)
    if not (current_user.can_admin("audiencias") or current_user.autoridad_id == audiencia.autoridad_id):
        flash("No tiene permiso para editar esta audiencia.", "warning")
        return redirect(url_for("edictos.list_active"))

    # Validar autoridad
    autoridad = audiencia.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria != "CIVIL FAMILIAR MERCANTIL LETRADO TCYA":
        flash("La categoría de audiencia no es CIVIL FAMILIAR MERCANTIL LETRADO TCYA.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Si viene el formulario
    form = AudienciaGenericaForm()
    if form.validate_on_submit():

        # Definir tiempo con la fecha y horas:minutos
        try:
            tiempo = datetime.combine(form.tiempo_fecha.data, form.tiempo_horas_minutos.data)
        except ValueError:
            flash("Error al definir el tiempo con la fecha y horas:minutos.", "warning")
            return redirect(url_for("audiencias.list_active"))

        # Actualizar registro
        audiencia.tiempo = tiempo
        audiencia.tipo_audiencia = safe_string(form.tipo_audiencia.data)
        audiencia.expediente = safe_string(form.expediente.data)
        audiencia.actores = safe_string(form.actores.data)
        audiencia.demandados = safe_string(form.demandados.data)
        audiencia.save()

        # Registrar en bitácora e ir al detalle
        bitacora = edit_success(audiencia)
        flash(bitacora.descripcion, 'success')
        return redirect(bitacora.url)

    # Prellenado del formulario
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    form.tiempo_fecha.data = autoridad.tiempo.date()
    form.tiempo_horas_minutos.data = autoridad.tiempo.time()
    form.tipo_audiencia.data = audiencia.tipo_audiencia
    form.expediente.data = audiencia.expediente
    form.actores.data = audiencia.actores
    form.demandados.data = audiencia.demandados
    return render_template('audiencias/edit_generica.jinja2', form=form, audiencia=audiencia)


@audiencias.route('/audiencias/edicion/mapo/<int:audiencia_id>', methods=['GET', 'POST'])
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def edit_mapo(audiencia_id):
    """Editar Audiencia MATERIA ACUSATORIO PENAL ORAL"""

    # Validar audiencia
    audiencia = Audiencia.query.get_or_404(audiencia_id)
    if not (current_user.can_admin("audiencias") or current_user.autoridad_id == audiencia.autoridad_id):
        flash("No tiene permiso para editar esta audiencia.", "warning")
        return redirect(url_for("edictos.list_active"))

    # Validar autoridad
    autoridad = audiencia.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria != "MATERIA ACUSATORIO PENAL ORAL":
        flash("La categoría de audiencia no es MATERIA ACUSATORIO PENAL ORAL.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Si viene el formulario
    form = AudienciaMapoForm()
    if form.validate_on_submit():

        # Definir tiempo con la fecha y horas:minutos
        try:
            tiempo = datetime.combine(form.tiempo_fecha.data, form.tiempo_horas_minutos.data)
        except ValueError:
            flash("Error al definir el tiempo con la fecha y horas:minutos.", "warning")
            return redirect(url_for("audiencias.list_active"))

        # Actualizar registro
        audiencia.tiempo = tiempo
        audiencia.tipo_audiencia = safe_string(form.tipo_audiencia.data)
        audiencia.sala = safe_string(form.sala.data)
        audiencia.caracter = safe_string(form.caracter.data)
        audiencia.causa_penal = safe_string(form.causa_penal.data)
        audiencia.delitos = safe_string(form.delitos.data)
        audiencia.save()

        # Registrar en bitácora e ir al detalle
        bitacora = edit_success(audiencia)
        flash(bitacora.descripcion, 'success')
        return redirect(bitacora.url)

    # Prellenado del formulario
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    form.tiempo_fecha.data = autoridad.tiempo.date()
    form.tiempo_horas_minutos.data = autoridad.tiempo.time()
    form.tipo_audiencia.data = audiencia.tipo_audiencia
    form.sala.data = audiencia.sala
    form.caracter.data = audiencia.caracter
    form.causa_penal.data = audiencia.causa_penal
    form.delitos.data = audiencia.delitos
    return render_template('audiencias/edit_mapo.jinja2', form=form, audiencia=audiencia)


@audiencias.route('/audiencias/edicion/dipe/<int:audiencia_id>', methods=['GET', 'POST'])
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def edit_dipe(audiencia_id):
    """Editar Audiencia DISTRITALES"""

    # Validar audiencia
    audiencia = Audiencia.query.get_or_404(audiencia_id)
    if not (current_user.can_admin("audiencias") or current_user.autoridad_id == audiencia.autoridad_id):
        flash("No tiene permiso para editar esta audiencia.", "warning")
        return redirect(url_for("edictos.list_active"))

    # Validar autoridad
    autoridad = audiencia.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria != "DISTRITALES":
        flash("La categoría de audiencia no es DISTRITALES.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Si viene el formulario
    form = AudienciaDipeForm()
    if form.validate_on_submit():

        # Definir tiempo con la fecha y horas:minutos
        try:
            tiempo = datetime.combine(form.tiempo_fecha.data, form.tiempo_horas_minutos.data)
        except ValueError:
            flash("Error al definir el tiempo con la fecha y horas:minutos.", "warning")
            return redirect(url_for("audiencias.list_active"))

        # Actualizar registro
        audiencia.tiempo = tiempo
        audiencia.tipo_audiencia = safe_string(form.tipo_audiencia.data)
        audiencia.expediente = safe_string(form.expediente.data)
        audiencia.actores = safe_string(form.actores.data)
        audiencia.demandados = safe_string(form.demandados.data)
        audiencia.toca = safe_string(form.toca.data)
        audiencia.expediente_origen = safe_string(form.expediente_origen.data)
        audiencia.imputados = safe_string(form.imputados.data)
        audiencia.save()

        # Registrar en bitácora e ir al detalle
        bitacora = edit_success(audiencia)
        flash(bitacora.descripcion, 'success')
        return redirect(bitacora.url)

    # Prellenado del formulario
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    form.tiempo_fecha.data = autoridad.tiempo.date()
    form.tiempo_horas_minutos.data = autoridad.tiempo.time()
    form.tipo_audiencia.data = audiencia.tipo_audiencia
    form.expediente.data = audiencia.expediente
    form.actores.data = audiencia.actores
    form.demandados.data = audiencia.demandados
    form.toca.data = audiencia.toca
    form.expediente_origen.data = audiencia.expediente_origen
    form.imputados.data = audiencia.imputados
    return render_template('audiencias/edit_dipe.jinja2', form=form, audiencia=audiencia)


@audiencias.route('/audiencias/edicion/sape/<int:audiencia_id>', methods=['GET', 'POST'])
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def edit_sape(audiencia_id):
    """Editar Audiencia SALAS"""

    # Validar audiencia
    audiencia = Audiencia.query.get_or_404(audiencia_id)
    if not (current_user.can_admin("audiencias") or current_user.autoridad_id == audiencia.autoridad_id):
        flash("No tiene permiso para editar esta audiencia.", "warning")
        return redirect(url_for("edictos.list_active"))

    # Validar autoridad
    autoridad = audiencia.autoridad
    if autoridad.estatus != "A":
        flash("El juzgado/autoridad no es activa.", "warning")
        return redirect(url_for("audiencias.list_active"))
    if autoridad.audiencia_categoria != "SALAS":
        flash("La categoría de audiencia no es SALAS.", "warning")
        return redirect(url_for("audiencias.list_active"))

    # Si viene el formulario
    form = AudienciaSapeForm()
    if form.validate_on_submit():

        # Definir tiempo con la fecha y horas:minutos
        try:
            tiempo = datetime.combine(form.tiempo_fecha.data, form.tiempo_horas_minutos.data)
        except ValueError:
            flash("Error al definir el tiempo con la fecha y horas:minutos.", "warning")
            return redirect(url_for("audiencias.list_active"))

        # Actualizar registro
        audiencia.tiempo = tiempo
        audiencia.tipo_audiencia = safe_string(form.tipo_audiencia.data)
        audiencia.expediente = safe_string(form.expediente.data)
        audiencia.actores = safe_string(form.actores.data)
        audiencia.demandados = safe_string(form.demandados.data)
        audiencia.toca = safe_string(form.toca.data)
        audiencia.expediente_origen = safe_string(form.expediente_origen.data)
        audiencia.delitos = safe_string(form.delitos.data)
        audiencia.origen = safe_string(form.origen.data)
        audiencia.save()

        # Registrar en bitácora e ir al detalle
        bitacora = edit_success(audiencia)
        flash(bitacora.descripcion, 'success')
        return redirect(bitacora.url)

    # Prellenado del formulario
    form.distrito.data = autoridad.distrito.nombre
    form.autoridad.data = autoridad.descripcion
    form.tiempo_fecha.data = autoridad.tiempo.date()
    form.tiempo_horas_minutos.data = autoridad.tiempo.time()
    form.tipo_audiencia.data = audiencia.tipo_audiencia
    form.expediente.data = audiencia.expediente
    form.actores.data = audiencia.actores
    form.demandados.data = audiencia.demandados
    form.toca.data = audiencia.toca
    form.expediente_origen.data = audiencia.expediente_origen
    form.delitos.data = audiencia.delitos
    form.origen.data = audiencia.origen
    return render_template('audiencias/edit_sape.jinja2', form=form, audiencia=audiencia)


def delete_success(audiencia):
    """Mensaje de éxito al eliminar una audiencia"""
    bitacora = Bitacora(
        modulo=MODULO,
        usuario=current_user,
        descripcion=safe_message("Eliminada la audiencia del " + audiencia.tiempo.strftime('%Y-%m-%d %H:%M')),
        url=url_for('audiencias.detail', audiencia_id=audiencia.id),
    )
    bitacora.save()
    return bitacora


@audiencias.route('/audiencias/eliminar/<int:audiencia_id>')
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def delete(audiencia_id):
    """ Eliminar Audiencia """
    audiencia = Audiencia.query.get_or_404(audiencia_id)
    if audiencia.estatus == 'A':
        if current_user.can_admin("audiencias") or current_user.autoridad_id == audiencia.autoridad_id:
            audiencia.delete()
            bitacora = delete_success(audiencia)
            flash(bitacora.descripcion, 'success')
        else:
            flash("No tiene permiso para eliminar.", "warning")
    return redirect(url_for('audiencias.detail', audiencia_id=audiencia.id))


def recover_success(audiencia):
    """Mensaje de éxito al recuperar una audiencia"""
    bitacora = Bitacora(
        modulo=MODULO,
        usuario=current_user,
        descripcion=safe_message("Recuperada la audiencia del " + audiencia.tiempo.strftime('%Y-%m-%d %H:%M')),
        url=url_for('audiencias.detail', audiencia_id=audiencia.id),
    )
    bitacora.save()
    return bitacora


@audiencias.route('/audiencias/recuperar/<int:audiencia_id>')
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def recover(audiencia_id):
    """ Recuperar Audiencia """
    audiencia = Audiencia.query.get_or_404(audiencia_id)
    if audiencia.estatus == 'B':
        if current_user.can_admin("audiencias") or current_user.autoridad_id == audiencia.autoridad_id:
            audiencia.recover()
            bitacora = recover_success(audiencia)
            flash(bitacora.descripcion, 'success')
        else:
            flash("No tiene permiso para eliminar.", "warning")
    return redirect(url_for('audiencias.detail', audiencia_id=audiencia.id))
