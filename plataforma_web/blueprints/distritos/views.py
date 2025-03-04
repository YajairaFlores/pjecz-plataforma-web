"""
Distritos, vistas
"""
from flask import Blueprint, flash, render_template, redirect, url_for
from flask_login import current_user, login_required

from lib.safe_string import safe_message

from plataforma_web.blueprints.bitacoras.models import Bitacora
from plataforma_web.blueprints.distritos.models import Distrito
from plataforma_web.blueprints.distritos.forms import DistritoForm
from plataforma_web.blueprints.modulos.models import Modulo
from plataforma_web.blueprints.permisos.models import Permiso
from plataforma_web.blueprints.usuarios.decorators import permission_required

MODULO = "DISTRITOS"

distritos = Blueprint("distritos", __name__, template_folder="templates")


@distritos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@distritos.route("/distritos")
def list_active():
    """Listado de Distritos activos"""
    return render_template(
        "distritos/list.jinja2",
        distritos=Distrito.query.filter(Distrito.estatus == "A").all(),
        titulo="Distritos",
        estatus="A",
    )


@distritos.route("/distritos/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Distritos inactivos"""
    return render_template(
        "distritos/list.jinja2",
        distritos=Distrito.query.filter(Distrito.estatus == "B").all(),
        titulo="Distritos inactivos",
        estatus="B",
    )


@distritos.route("/distrito/<int:distrito_id>")
def detail(distrito_id):
    """Detalle de un Distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    return render_template("distritos/detail.jinja2", distrito=distrito)


@distritos.route("/distritos/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Distrito"""
    form = DistritoForm()
    if form.validate_on_submit():
        distrito = Distrito(nombre=form.nombre.data)
        distrito.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo distrito {distrito.nombre}"),
            url=url_for("distritos.detail", distrito_id=distrito.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("distritos/new.jinja2", form=form)


@distritos.route("/distritos/edicion/<int:distrito_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(distrito_id):
    """Editar Distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    form = DistritoForm()
    if form.validate_on_submit():
        distrito.nombre = form.nombre.data
        distrito.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado distrito {distrito.nombre}"),
            url=url_for("distritos.detail", distrito_id=distrito.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.nombre.data = distrito.nombre
    return render_template("distritos/edit.jinja2", form=form, distrito=distrito)


@distritos.route("/distritos/eliminar/<int:distrito_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(distrito_id):
    """Eliminar Distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    if distrito.estatus == "A":
        distrito.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado distrito {distrito.nombre}"),
            url=url_for("distritos.detail", distrito_id=distrito.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return redirect(url_for("distritos.detail", distrito_id=distrito.id))


@distritos.route("/distritos/recuperar/<int:distrito_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(distrito_id):
    """Recuperar Distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    if distrito.estatus == "B":
        distrito.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado distrito {distrito.nombre}"),
            url=url_for("distritos.detail", distrito_id=distrito.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return redirect(url_for("distritos.detail", distrito_id=distrito.id))
