# pjecz-plataforma-web

Administrador de contenidos del sitio web del PJECZ.

## Entorno Virtual con Python 3.6 o superior

Crear el entorno virtual dentro de la copia local del repositorio, con

    python -m venv venv

O con virtualenv

    virtualenv -p python3 venv

Active el entorno virtual, en Linux con...

    source venv/bin/activate

O en windows con

    venv/Scripts/activate

Verifique que haya el mínimo de paquetes con

    pip list

Actualice el pip de ser necesario

    pip install --upgrade pip

Y luego instale los paquetes que requiere Plataforma Web

    pip install -r requirements.txt

Verifique con

    pip list

## Configurar

Debe crear un archivo instance/settings.py que defina su configuración para desarrollo...

    # Flask
    SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxx'

    # Base de datos en SQLLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pjecz_plataforma_web.sqlite3'

    # Base de datos MariaDB
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://wronguser:badpassword@127.0.0.1/pjecz_plataforma_web'

O bien, puede guardar valores en un archivo .env como variables de entorno...

    # Flask
    FLASK_APP=plataforma_web.app
    FLASK_DEBUG=1
    SECRET_KEY=****************

    # Base de datos
    DB_USER=pjeczadmin
    DB_PASS=********
    DB_NAME=pjecz_plataforma_web
    DB_HOST=127.0.0.1

Y los obtiene en instance/settings.py con...

    import os
    DB_USER = os.environ.get("DB_USER", "wronguser")
    DB_PASS = os.environ.get("DB_PASS", "badpassword")
    DB_NAME = os.environ.get("DB_NAME", "pjecz_plataforma_web")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

## Cargar registros iniciales

Crear directorio seed

    mkdir seed

Copie los archivos CSV en seed.

Instale el comando click con

    pip install --editable .

Y ejecute la inicialización y alimentación

    plataforma_web db inicializar
    plataforma_web db alimentar

En el futuro, use reiniciar que es inicializar y alimentar

    plataforma_web db reiniciar

## Arrancar el Flask

En el entorno virtual cargue las variables de entorno

Para la línea de comandos de windows...

    set FLASK_APP=plataforma_web/app.py
    set FLASK_DEBUG=1

Para la power shell de windows...

    $env:FLASK_APP = "plataforma_web/app.py"
    $env:FLASK_DEBUG = 1

Para la terminal GNU/Linux...

    export FLASK_APP=plataforma_web.app
    export FLASK_DEBUG=1

Y ejecute Flask

    flask run

## Arrancar RQ worker

Las tareas en el fondo requieren un servicio Redis

Abra una terminal, cargue el entorno virtual y deje en ejecución el worker

    rq worker pjecz_plataforma_web

Estará vigilante de Redis

## Crear archivos PDF con pdfkit

Este paquete de python requiere que se instale wkhtmltopdf

    sudo dnf install wkhtmltopdf
