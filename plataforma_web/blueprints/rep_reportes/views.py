"""
Rep Reportes, vistas
"""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required
from plataforma_web.blueprints.roles.models import Permiso
from plataforma_web.blueprints.usuarios.decorators import permission_required

from plataforma_web.blueprints.rep_reportes.models import RepReporte
from plataforma_web.blueprints.rep_reportes.forms import RepReporteForm
from plataforma_web.blueprints.rep_resultados.models import RepResultado

rep_reportes = Blueprint("reportes", __name__, template_folder="templates")


@rep_reportes.before_request
@login_required
@permission_required(Permiso.VER_CUENTAS)
def before_request():
    """Permiso por defecto"""


@rep_reportes.route("/rep_reportes")
def list_active():
    """Listado de Reportes activos"""
    rep_reportes_activos = RepReporte.query.filter(RepReporte.estatus == "A").order_by(RepReporte.creado.desc()).limit(100).all()
    return render_template("rep_reportes/list.jinja2", rep_reportes=rep_reportes_activos, estatus="A")


@rep_reportes.route("/rep_reportes/inactivos")
@permission_required(Permiso.MODIFICAR_CUENTAS)
def list_inactive():
    """Listado de Reportes inactivos"""
    rep_reportes_inactivos = RepReporte.query.filter(RepReporte.estatus == "B").order_by(RepReporte.creado.desc()).limit(100).all()
    return render_template("rep_reportes/list.jinja2", rep_reportes=rep_reportes_inactivos, estatus="B")


@rep_reportes.route("/rep_reportes/<int:rep_reporte_id>")
def detail(rep_reporte_id):
    """Detalle de un Reporte"""
    rep_reporte = RepReporte.query.get_or_404(rep_reporte_id)
    rep_resultados = RepResultado.query.filter(RepResultado.reporte == rep_reporte).filter(RepResultado.estatus == "A").all()
    return render_template("rep_reportes/detail.jinja2", rep_reporte=rep_reporte, rep_resultados=rep_resultados)


@rep_reportes.route("/rep_reportes/nuevo", methods=["GET", "POST"])
@permission_required(Permiso.CREAR_CUENTAS)
def new():
    """Nuevo Reporte"""
    form = RepReporteForm()
    if form.validate_on_submit():
        rep_reporte = RepReporte(
            descripcion=form.descripcion.data,
            desde=form.desde.data,
            hasta=form.hasta.data,
            programado=form.programado.data,
            progreso=form.progreso.data,
        )
        rep_reporte.save()
        flash(f"Reporte {rep_reporte.descripcion} guardado.", "success")
        return redirect(url_for("reportes.detail", rep_reporte_id=rep_reporte.id))
    return render_template("rep_reportes/new.jinja2", form=form)


@rep_reportes.route("/rep_reportes/edicion/<int:rep_reporte_id>", methods=["GET", "POST"])
@permission_required(Permiso.MODIFICAR_CUENTAS)
def edit(rep_reporte_id):
    """Editar Reporte"""
    rep_reporte = RepReporte.query.get_or_404(rep_reporte_id)
    form = RepReporteForm()
    if form.validate_on_submit():
        rep_reporte.descripcion = form.descripcion.data
        rep_reporte.desde = form.desde.data
        rep_reporte.hasta = form.hasta.data
        rep_reporte.programado = form.programado.data
        rep_reporte.progreso = form.progreso.data
        rep_reporte.save()
        flash(f"Reporte {rep_reporte.descripcion} guardado.", "success")
        return redirect(url_for("reportes.detail", rep_reporte_id=rep_reporte.id))
    form.descripcion.data = rep_reporte.descripcion
    form.desde.data = rep_reporte.desde
    form.hasta.data = rep_reporte.hasta
    form.programado.data = rep_reporte.programado
    form.progreso.data = rep_reporte.progreso
    return render_template("rep_reportes/edit.jinja2", form=form, rep_reporte=rep_reporte)


@rep_reportes.route("/rep_reportes/eliminar/<int:rep_reporte_id>")
@permission_required(Permiso.MODIFICAR_CUENTAS)
def delete(rep_reporte_id):
    """Eliminar Reporte"""
    rep_reporte = RepReporte.query.get_or_404(rep_reporte_id)
    if rep_reporte.estatus == "A":
        rep_reporte.delete()
        flash(f"Reporte {rep_reporte.descripcion} eliminado.", "success")
    return redirect(url_for("rep_reportes.detail", rep_reporte_id=rep_reporte.id))


@rep_reportes.route("/rep_reportes/recuperar/<int:rep_reporte_id>")
@permission_required(Permiso.MODIFICAR_CUENTAS)
def recover(rep_reporte_id):
    """Recuperar Reporte"""
    rep_reporte = RepReporte.query.get_or_404(rep_reporte_id)
    if rep_reporte.estatus == "B":
        rep_reporte.recover()
        flash(f"Reporte {rep_reporte.descripcion} recuperado.", "success")
    return redirect(url_for("rep_reportes.detail", rep_reporte_id=rep_reporte.id))
