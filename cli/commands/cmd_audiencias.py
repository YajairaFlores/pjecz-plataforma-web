"""
Audiencias

- alimentar: Alimentar desde un archivo CSV con el nombre de la clave de la autoridad
- respaldar: Respaldar a un archivo CSV
"""
from datetime import datetime
from pathlib import Path
import csv
import click

from lib.safe_string import safe_string
from lib.time_utc import local_to_utc, utc_to_local_str

from plataforma_web.app import create_app
from plataforma_web.extensions import db

from plataforma_web.blueprints.audiencias.models import Audiencia
from plataforma_web.blueprints.autoridades.models import Autoridad

app = create_app()
db.app = app


@click.group()
def cli():
    """Audiencias"""


@click.command()
@click.argument("entrada_csv")
def alimentar(entrada_csv):
    """Alimentar desde un archivo CSV con el nombre de la clave de la autoridad"""
    ruta = Path(entrada_csv)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        return
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        return
    clave = ruta.name[:-len(ruta.suffix)]
    autoridad = Autoridad.query.filter(Autoridad.clave == clave).first()
    if autoridad is None:
        click.echo(f"AVISO: Con el nombre del archivo {ruta.name} no hay clave en autoridades.")
        return
    if autoridad.es_jurisdiccional is False:
        click.echo("AVISO: La autoridad no es jurisdiccional")
        return
    click.echo("Alimentando audiencias...")
    contador = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            try:
                tiempo = datetime.strptime(row["tiempo"], "%Y-%m-%d %H:%M")
            except (IndexError, ValueError, KeyError):
                try:
                    tiempo = datetime.strptime(row["tiempo"], "%Y-%m-%d %H:%M:%S")
                except (IndexError, ValueError, KeyError):
                    click.echo("  Tiempo incorrecto, se omite" + str(row))
                    continue
            try:
                tipo_audiencia = safe_string(row["tipo_audiencia"])
            except KeyError:
                tipo_audiencia = "NO DEFINIDO"
            try:
                exp = row["expediente"].strip()
                if len(exp) > 60:
                    expediente = exp[:60] + "..."
                else:
                    expediente = exp
            except KeyError:
                expediente = ""
            try:
                actores = safe_string(row["actores"])
            except KeyError:
                actores = ""
            try:
                demandados = safe_string(row["demandados"])
            except KeyError:
                demandados = ""
            try:
                sala = safe_string(row["sala"])
            except KeyError:
                sala = ""
            try:
                caracter = safe_string(row["caracter"])
                if caracter not in ("PUBLICA", "PRIVADA"):
                    caracter = None
            except KeyError:
                caracter = None
            try:
                causa_penal = safe_string(row["causa_penal"])
            except KeyError:
                causa_penal = ""
            try:
                delitos = safe_string(row["delitos"])
            except KeyError:
                delitos = ""
            try:
                toca = safe_string(row["toca"])
            except KeyError:
                toca = ""
            try:
                expediente_origen = safe_string(row["expediente_origen"])
            except KeyError:
                expediente_origen = ""
            try:
                imputados = safe_string(row["imputados"])
            except KeyError:
                imputados = ""
            try:
                origen = safe_string(row["origen"])
            except KeyError:
                origen = ""
            Audiencia(
                autoridad=autoridad,
                tiempo=local_to_utc(tiempo),
                tipo_audiencia=tipo_audiencia,
                expediente=expediente,
                actores=actores,
                demandados=demandados,
                sala=sala,
                caracter=caracter,
                causa_penal=causa_penal,
                delitos=delitos,
                toca=toca,
                expediente_origen=expediente_origen,
                imputados=imputados,
                origen=origen,
            ).save()
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"{contador} audiencias alimentadas.")


@click.command()
@click.option("--autoridad-id", default=None, type=int, help="ID de la autoridad")
@click.option("--autoridad-clave", default="", type=str, help="Clave de la autoridad")
@click.option("--desde", default="", type=str, help="Fecha de inicio AAAA-MM-DD")
@click.option("--output", default="audiencias.csv", type=str, help="Archivo CSV a escribir")
def respaldar(autoridad_id, autoridad_clave, desde, output):
    """Respaldar a un archivo CSV"""
    ruta = Path(output)
    if ruta.exists():
        click.echo(f"AVISO: {ruta.name} existe, no voy a sobreescribirlo.")
        return
    if autoridad_id:
        autoridad = Autoridad.query.get(autoridad_id)
    elif autoridad_clave:
        autoridad = Autoridad.query.filter_by(clave=autoridad_clave).first()
    else:
        autoridad = None
    if autoridad is not None and autoridad.es_jurisdiccional is False:
        click.echo("AVISO: La autoridad no es jurisdiccional")
        return
    if desde != "":
        try:
            desde_fecha = datetime.strptime(desde, "%Y-%m-%d")
        except ValueError as mensaje:
            click.echo(f"AVISO: Fecha de inicio es incorrecta: {mensaje}")
            return
    else:
        desde_fecha = None
    click.echo("Respaldando audiencias...")
    contador = 0
    audiencias = Audiencia.query.filter_by(estatus="A")
    if autoridad is not None:
        audiencias = audiencias.filter(Audiencia.autoridad == autoridad)
    if desde_fecha is not None:
        audiencias = audiencias.filter(Audiencia.tiempo >= desde_fecha)
    audiencias = audiencias.order_by(Audiencia.tiempo).all()
    with open(ruta, "w", encoding="utf8") as puntero:
        respaldo = csv.writer(puntero)
        respaldo.writerow(
            [
                "autoridad_clave",
                "tiempo",
                "tipo_audiencia",
                "expediente",
                "actores",
                "demandados",
                "sala",
                "caracter",
                "causa_penal",
                "delitos",
                "toca",
                "expediente_origen",
                "imputados",
                "origen",
            ]
        )
        for audiencia in audiencias:
            respaldo.writerow(
                [
                    audiencia.autoridad.clave,
                    utc_to_local_str(audiencia.tiempo),
                    audiencia.tipo_audiencia,
                    audiencia.expediente,
                    audiencia.actores,
                    audiencia.demandados,
                    audiencia.sala,
                    audiencia.caracter,
                    audiencia.causa_penal,
                    audiencia.delitos,
                    audiencia.toca,
                    audiencia.expediente_origen,
                    audiencia.imputados,
                    audiencia.origen,
                ]
            )
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"Respaldados {contador} audiencias en {ruta.name}")


cli.add_command(alimentar)
cli.add_command(respaldar)
