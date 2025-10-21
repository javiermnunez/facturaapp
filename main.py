# -*- coding: utf-8 -*-
#Importación de librerias para trabajar
import sys
import os
import shutil #nuevo
import base64
import zlib
from os import remove
from werkzeug.utils import secure_filename
from flask import Flask,flash,request,redirect,send_file,render_template, jsonify
from flask import redirect, url_for
#from flask.globals import session
from flask_profiler import Profiler
#import DatabaseConnection
from clases.Usuario import Usuario
import mysql.connector #nuevo
from flaskext.mysql import MySQL
from datetime import datetime
from email.message import EmailMessage
from gevent.pywsgi import WSGIServer
import smtplib
#import pandas as pd
import time

#Beta
servidorIp = "0.0.0.0"
#Casa
#servidorIp = "192.168.1.4"
#servidorIp='localhost'
# Obtener la ruta al directorio actual del script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Agregar el directorio al sys.path
sys.path.append(current_dir)
carpetaRepositorio = current_dir+"\\datos\\beta\\repositorio"
carpetaAprobados = current_dir+"\\datos\\beta\\aprobados"
carpetaLiberados = current_dir+"\\datos\\beta\\liberados"

max_size = 10485760 #10mb
#Declaración  de variable que hace referencia a la carpeta contenedora para alojar los archivos
FILE_CONTAINER = './cont/'

app = Flask(__name__, template_folder='templates')
app.debug = False
app.config['FILE_CONTAINER'] = FILE_CONTAINER
app.config['flask_profiler'] = {
    "enabled": app.config.get("DEBUG"),
    "storage": {
        "engine": "sqlite"
    },
    "basicAuth":{
        "enabled": True,
        "username": "admin",
        "password": "admin"
    },
    "ignore": [
        "^/static/.*"
    ]
}
profiler = Profiler()
profiler.init_app(app)
app.secret_key = "vigoray"
#Base de datos de Microsoft MSQL SERVER:
#conexion = mysql.connector.connect(host="localhost",port="3307", user="root", passwd="vigoray",database="personas") #print("¡Conexión exitosa!")

#Base de datos Xampp:
#conexion = mysql.connector.connect(host="localhost",port="3306", user="root", passwd="",database="personas") #print("¡Conexión exitosa!")

mysql = MySQL()


app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'vigoray'
app.config['MYSQL_DATABASE_DB'] = 'personas'
app.config['MYSQL_DATABASE_PORT'] = 3307
mysql.init_app(app)

def buscarCentros():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `centro` order by `detalle`;")
    centros = cursor.fetchall()
    conexion.commit()
    return centros

def buscarProveedores():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `proveedores` order by `detalle`;")
    proveedores = cursor.fetchall()
    conexion.commit()
    return proveedores

def buscarProveedoresId(id):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `proveedores` where `id_proveedor` = {id};")
    proveedor = cursor.fetchall()
    conexion.commit()
    return proveedor

def buscarProveedoresRecientesId(id):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `recientes` where `id_proveedor` = {id};")
    proveedor = cursor.fetchall()
    conexion.commit()
    return proveedor


def enviarMail(asunto,destinatario, mensaje):
    destinatario = "jmn@betalab.com.ar"
    try:
        em = EmailMessage()
        em["To"] = destinatario
        em["Subject"] = asunto
        em.set_content(mensaje)
        
        with smtplib.SMTP("outlook.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login("beta@betalab.com.ar", "Sanjuan2266")
            smtp.sendmail("beta@betalab.com.ar", destinatario, em.as_string())
            return True
    except Exception as e:
        return (f"Error al enviar el correo: {e}")
        
def buscar_duplicados(registros):
    # Diccionario para almacenar los registros únicos basados en el campo 'cuit'
    registros_unicos = {}
    # Lista para almacenar los registros duplicados
    duplicados = []

    for registro in registros:
        cuit = registro[1]

        # Verificar si ya existe un registro con el mismo 'cuit'
        if cuit in registros_unicos:
            # Agregar a la lista de duplicados si ya existe
            duplicados.append(registro)
        else:
            # Agregar al diccionario de registros únicos si es el primero
            registros_unicos[cuit] = registro

    return duplicados

def buscar_duplicados_y_borrar(registros):
    # Diccionario para almacenar los registros únicos basados en el campo 'cuit'
    registros_unicos = {}
    # Lista para almacenar los registros duplicados
    duplicados = []

    for registro in registros:
        cuit = registro[1]

        # Verificar si ya existe un registro con el mismo 'cuit'
        if cuit in registros_unicos:
            # Agregar a la lista de duplicados si ya existe
            borrar_proveedor(registro[0])
        else:
            # Agregar al diccionario de registros únicos si es el primero
            registros_unicos[cuit] = registro

def generarCarpetas():
    try:
        os.makedirs(carpetaRepositorio, exist_ok=True)
        print(f'Carpeta creada en: {carpetaRepositorio}')
    except FileExistsError:
        print(f'La carpeta ya existe en: {carpetaRepositorio}')
    except Exception as e:
        print(f'Error al crear la carpeta: {e}')
    try:
        os.makedirs(carpetaAprobados, exist_ok=True)
        print(f'Carpeta creada en: {carpetaAprobados}')
    except FileExistsError:
        print(f'La carpeta ya existe en: {carpetaAprobados}')
    except Exception as e:
        print(f'Error al crear la carpeta: {e}')
    try:
        os.makedirs(carpetaLiberados, exist_ok=True)
        print(f'Carpeta creada en: {carpetaLiberados}')
    except FileExistsError:
        print(f'La carpeta ya existe en: {carpetaLiberados}')
    except Exception as e:
        print(f'Error al crear la carpeta: {e}')
generarCarpetas()

def rutaArchivo(id_archivo):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlArchivo = f"select * from archivos where id_archivo = {id_archivo};"
    cursor.execute(sqlArchivo)
    archivo = cursor.fetchall()
    conexion.commit()
    ruta = rf'{decodificar(archivo[0][1])}'
    
    if os.path.exists(ruta):
        print("El archivo existe en la ruta especificada.")
    else:
        print("Error: El archivo no se encuentra en la ruta especificada.")

    return ruta
    
def rutaArchivoAnexo(id_archivo):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlArchivo = f"select * from comprobantes where id_anexo = {id_archivo};"
    cursor.execute(sqlArchivo)
    archivo = cursor.fetchall()
    conexion.commit()
    ruta = rf'{decodificar(archivo[0][5])}'
    return ruta



def buscarArchivoId(id_archivo):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlArchivo = f"select * from archivos where id_archivo = {id_archivo};"
    cursor.execute(sqlArchivo)
    archivo = cursor.fetchall()
    conexion.commit()
    return archivo

def buscarArchivo(nro,cuit):
    salida = 1
    print("numero "+nro)
    print("proveedor "+cuit)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlArchivo = f"select * from archivos where `nro` = '{nro}' AND `cuit` = '{cuit}'"
    cursor.execute(sqlArchivo)
    archivo = cursor.fetchall()
    conexion.commit()
    print(len(archivo))
    if len(archivo) == 0:
        salida = 0
    return salida

def buscarArchivoPorRuta(ruta):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlArchivo = f"select * from archivos where ruta = '{ruta}';"
    cursor.execute(sqlArchivo)
    archivo = cursor.fetchall()
    conexion.commit()
    return archivo

def renombrarArchivo(rutaArchivoOriginal,nombreNuevo):
    # Ruta del archivo actual

    ruta_original = rutaArchivoOriginal

    # Nuevo nombre del archivo
    nuevo_nombre = nombreNuevo

    # Combinar la ruta original con el nuevo nombre
    ruta_nueva = os.path.join(os.path.dirname(ruta_original), nuevo_nombre)

    # Cambiar el nombre del archivo
    os.rename(ruta_original, ruta_nueva)

def buscarAprovadosControl():
    aprobadosC = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos where estado='APROBADO';")
    apro = cursor.fetchall()
    conexion.commit()
    for registro in apro:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        aprobado = registro[12]
        cuit = registro[13]
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,aprobado,cuit])

    return aprobadosC

def buscarLiberadosP():
    aprobadosC = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM archivos WHERE (estado='LIBERADO' OR estado='FINALIZADO' OR estado='Ok_IMPUESTOS') AND destino='PROVEEDORES';")
    apro = cursor.fetchall()
    conexion.commit()
    for registro in apro:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        cuit = registro[13]
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,cuit])

    return aprobadosC

def buscarLiberadosS():
    aprobadosC = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos where (estado='LIBERADO' OR estado='FINALIZADO') AND(destino='SERVICIOS');")
    apro = cursor.fetchall()
    conexion.commit()
    for registro in apro:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        cuit = registro[13]
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,cuit])

    return aprobadosC

def buscarLiberadosD():
    aprobadosC = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos where (estado='LIBERADO' OR estado='FINALIZADO') AND(destino='DIRECTO');")
    apro = cursor.fetchall()
    conexion.commit()
    for registro in apro:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        cuit = registro[13]
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,cuit])

    return aprobadosC

def buscarLiberadosC(idU):
    aprobadosC = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    #cursor.execute(f"SELECT * FROM archivos where estado='LIBERADO' AND(usuario='{idU}');")
    cursor.execute(f"SELECT * FROM archivos where estado='LIBERADO';")
    apro = cursor.fetchall()
    conexion.commit()
    for registro in apro:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        liberado = registro[11]
        cuit = registro[13]
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,liberado,cuit])

    return aprobadosC

def buscarLiberadosI():
    aprobadosC = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM archivos WHERE estado='IMPUESTOS';")
    apro = cursor.fetchall()
    conexion.commit()
    for registro in apro:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        cuit = registro[13]
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,cuit])

    return aprobadosC

def buscarLiberadosCentro(centro):

    aprobadosC = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos WHERE (estado='LIBERADO' OR estado='FINALIZADO' OR estado= 'IMPUESTOS' OR estado= 'OK_IMPUESTOS') AND(centro='{centro}');")
    apro = cursor.fetchall()
    conexion.commit()
    for registro in apro:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        liberado = registro[11]
        cuit = registro[13]
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,liberado,cuit])

    return aprobadosC


def volverInicioOrigen(usuario, password,origen):
    sqlUsuario = buscarUsuarioPass(usuario,password)
    centros = buscarCentros()
    proveedores = buscarProveedores()
    print('string:'+str(sqlUsuario))
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
        
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == "EMPLEADO" or usuarioO.roll == "JEFE":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarArchivosApro(usuarioO.centro)
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template(f'{origen}.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
        if usuarioO.roll == "CONTROL"or (usuarioO.roll == "JEFE" and usuarioO.centro == "O510"):
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarAprovadosControl()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            if origen == "liberados":
                sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
                sqlLiberados = buscarLiberadosC(usuarioO.id)
                listaArchivos = sqlArchivosRepo
                listaLiberados = sqlLiberados
                return render_template('liberados.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, liberados = listaLiberados, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
            return render_template(f'{origen}.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)   
        if usuarioO.roll == "PROVEEDORES":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosP()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
        
        if usuarioO.roll == "SERVICIOS":
            sqlArchivosApro = buscarLiberadosS()
          
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)   
        if usuarioO.roll == "DIRECTO":
            sqlArchivosApro = buscarLiberadosD()
            
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)         
        if usuarioO.roll == "IMPUESTOS":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosI()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores) 
    else:
                flash('Error.')
    return redirect('/')

def buscarArchivosRepo(usuario,centro):
    print(centro)
    repositorio = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    if usuario.roll == "EMPLEADO":
        cursor.execute(f"SELECT * FROM archivos where `centro`='{centro}' AND (usuario='{usuario.id}')AND (estado='NO_APROBADO');")
    if usuario.roll == "CONTROL":
        cursor.execute(f"SELECT * FROM archivos where usuario='{usuario.id}' AND (estado='NO_APROBADO');")
    if usuario.roll == "JEFE":
        cursor.execute(f"SELECT * FROM archivos where `centro`='{centro}' AND (estado='NO_APROBADO');")
    if usuario.roll == "PROVEEDORES":
        cursor.execute(f"SELECT * FROM archivos where `centro`='{centro}' AND (usuario='{usuario.id}')AND (estado='NO_APROBADO');")
    if usuario.roll == "SERVICIOS":
        cursor.execute(f"SELECT * FROM archivos where `centro`='{centro}' AND (usuario='{usuario.id}')AND (estado='NO_APROBADO');")
    if usuario.roll == "DIRECTO":
        cursor.execute(f"SELECT * FROM archivos where `centro`='{centro}' AND (usuario='{usuario.id}')AND (estado='NO_APROBADO');")
    if usuario.roll == "IMPUESTOS":
        cursor.execute(f"SELECT * FROM archivos where `centro`='{centro}' AND (usuario='{usuario.id}')AND (estado='NO_APROBADO');")
    repo = cursor.fetchall()
    conexion.commit()
    for registro in repo:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        cuit = registro[13]
        na = registro[14]
        
        repositorio.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,cuit,na])
    print(repo)
    return repositorio

def buscarArchivosApro(centro):
    aprobados = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos where `centro`='{centro}' AND (estado='APROBADO');")
    apro = cursor.fetchall()
    conexion.commit()
    for registro in apro:
        id = registro[0]
        ruta = decodificar(registro[1])
        fecha = registro[2]
        usuario = registro[3]
        proveedor =registro[4]
        centro = registro[5]
        cae = registro[6]
        estado = registro[7]
        nombre = registro[8]
        fechaFC = registro[9]
        detalle = registro[10]
        aprobado = registro[12]
        cuit = registro[13]
        na = registro[14]
        aprobados.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,aprobado,cuit,na])

    return aprobados



@app.route('/noLogin')
def noLogin():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container-fluid">
    <dic class="row">
    <div class=" col-md-6 offset-md-3 text-center">
    <h1>Requiere inicio de sesión.</h1>
    <a class="btn btn-primary" href="/">Volver</a>
    </div>
    </div>
     </body> """

@app.route('/enviarContrasenia', methods=['POST'])
def enviarContrasenia():
    mail = request.form['mail']
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `mail` = '{mail}';")
    usuario = cursor.fetchall()
    conexion.commit()
    if len(usuario) == 0:
        mensaje = "Usuario no encontrado."
    else:
        enviarMail(f"Recuperar contraseña usuario: {usuario[0][5]}",mail,f"Contraseña: {usuario[0][6]}")
        mensaje = "Se envío mail con la contraseña actual."
    flash(mensaje)
    return redirect("/")

#para importar archivos xlsx de proveedores (deshabilitado).
"""
def leer_archivo_xlsx(archivo): #busca el archivo y lo ingresa a la base de datos
    if archivo == "proveedores":
        nombre_archivo = "proveedores.xlsx"
    
        try:
            # Leer el archivo Excel
            df = pd.read_excel(nombre_archivo)

            # Obtener los registros como una lista de diccionarios
            registros = df.to_dict(orient='records')
        
            contador = 0
        
            for r in registros:
                cuit = str(r['CUIT'])
                cuit = cuit[:2]+"-"+cuit[2:10]+"-"+cuit[-1]
                print(f"CUIT: {cuit} DETALLE: {r['DETALLE']} CODINT: {r['COD']}")
                if verificarCuit(cuit):
                    conexion = mysql.connect()
                    cursor = conexion.cursor()
                    sqlUsuario = f"INSERT INTO `proveedores` (`id_proveedor`, `cuit`, `detalle`, `cod`) VALUES (NULL, '{cuit}', '{r['DETALLE']}', '{r['COD']}');"
                    cursor.execute(sqlUsuario)
                    conexion.commit()
                    contador = contador+1
                print(contador)    
            return registros
        except Exception as e:
            print(f"Error al leer el archivo {nombre_archivo}: {e}")

    if archivo == "centros":
        nombre_archivo = "centros.xlsx"
        try:
            # Leer el archivo Excel
            df = pd.read_excel(nombre_archivo)

            # Obtener los registros como una lista de diccionarios
            registros = df.to_dict(orient='records')
        
            contador = 0
        
            for r in registros:
                codigo = str(r['codigo'])
                detalle = str(r['detalle'])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                sqlUsuario = f"INSERT INTO `centro` (`id_centro`, `cod`, `detalle`) VALUES (NULL, '{codigo}', '{detalle}');"
                cursor.execute(sqlUsuario)
                conexion.commit()
                contador = contador+1
            print(contador)    
            return registros      

        except Exception as e:
            print(f"Error al leer el archivo {nombre_archivo}: {e}")
        


@app.route('/actualizar_bd_proveedores')
def actualizarProveedoresBD():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlUsuario = "delete from proveedores"
    cursor.execute(sqlUsuario)
    conexion.commit()
    unaLista = []
    unaLista = leer_archivo_xlsx("proveedores")
    salida = "" 
    
    return f...
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container-fluid">
    <dic class="row">
    <div class=" col-md-6 offset-md-3 text-center">
    <h1>¿Se envió mail?</h1>
    <h1>Se actualizaron: </h1>
    <h3>{salida}</h3>
    <a class="btn btn-primary" href="/">Volver</a>
    </div>
    </div>
     </body> ...

@app.route('/actualizar_bd_centros')
def actualizarCentrosBD():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlUsuario = "delete from centro"
    cursor.execute(sqlUsuario)
    conexion.commit()
    unaLista = []
    unaLista = leer_archivo_xlsx("centros")
    salida = "" 
    return f...
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container-fluid">
    <dic class="row">
    <div class=" col-md-6 offset-md-3 text-center">
    <h1>¿Se envió mail?</h1>
    <h1>Se actualizaron: </h1>
    <h3>{salida}</h3>
    <a class="btn btn-primary" href="/">Volver</a>
    </div>
    </div>
     </body> 
"""

@app.route('/mail')
def mail():

    resultado = enviarMail("Prueba","jmn@betalab.com.ar", "Hola, este es el mensaje.")
        
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container-fluid">
    <dic class="row">
    <div class=" col-md-6 offset-md-3 text-center">
    <h1>¿Se envió mail?</h1>
    <h2>{resultado}</h2>
   
    <a class="btn btn-primary" href="/">Volver</a>
    </div>
    </div>
     </body> """


#Función para la eliminacion de archivos 
@app.route('/eliminarArchivo', methods=['POST'])
def eliminarArchivo():
    origen = request.form['origen']
    ruta = request.form['archivo']
    id_usuario = request.form['id']
    borrar_archivo(ruta)
    
    # Buscar el usuario
    sql_usuario = buscarUsuario(id_usuario)
    usuario = ""
    contrasenia = ""
    if sql_usuario and sql_usuario != "()" and sql_usuario != "[]":
        # Crear el objeto Usuario si se encuentra
        usuario_o = Usuario(sql_usuario[0][0],sql_usuario[0][1], sql_usuario[0][2], sql_usuario[0][3],
                            sql_usuario[0][4], sql_usuario[0][5], sql_usuario[0][6], sql_usuario[0][7])
        
        # Redirigir a la URL "/xepositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
    # Manejar el caso en el que no se encuentra el usuario
    redirect('/repositorio')
    return volverInicioOrigen(usuario,contrasenia,origen)

#Función para la eliminacion de archivos 
@app.route('/eliminarAnexo', methods=['POST'])
def eliminarAnexo():
    borrar_anexo_SQL(request.form['anexo'])
    flash("Se elimino el anexo correctamente.")
    rutas = []
    id = request.form['id']
    print("usuario id: "+id)
    usuario = buscarUsuario(id)
    id_archivo = request.form['id_archivo']
    rutas = buscarAnexos(id_archivo)

    return render_template("anexos.html" , anexos = rutas, usuario = usuario)

#Funcion para la descarga de archivos
@app.route('/download_file/<filename>')
def return_files_tut(filename):
    file_path = FILE_CONTAINER + filename
    print(file_path)
    return send_file(file_path, as_attachment=True, attachment_filename='')
#-------------------------------------------------------------------------------------------------------
def buscarUsuario(id): #nuevo
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `id`={id}")
    usuario = cursor.fetchall()
    conexion.commit()
    
    return usuario

def buscarUsuarioPass(usuario,contrasenia): #nuevo
    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where mail='{usuario}' AND (contrasenia='{contrasenia}')")
    usuarioT = cursor.fetchall()

    conexion.commit()
    
    return usuarioT

def borrar_archivo(ruta_completa):
    try:
        os.remove(ruta_completa)
        borrar_archivo_SQL(ruta_completa)
        print(f"El archivo en {ruta_completa} ha sido eliminado exitosamente.")
        
    except OSError as e:
        print(f"Error al eliminar el archivo en {ruta_completa}: {e}")

def borrar_archivo_SQL(ruta):
    unaRuta = codificar(ruta)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    
    try:
        cursor.execute(f"DELETE FROM `archivos` WHERE `archivos`.`ruta` = '{unaRuta}';")
        conexion.commit()
        print("Borra archivo SQL:", ruta)
        print("Codificada:", unaRuta)

        # Obtener el número de filas afectadas
        num_filas_afectadas = cursor.rowcount
        print(f"Número de filas afectadas: {num_filas_afectadas}")

    except Exception as e:
        print(f"Error al borrar el archivo SQL: {e}")

    finally:
        cursor.close()

def borrar_anexo_SQL(id_anexo):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    
    try:
        cursor.execute(f"DELETE FROM `comprobantes` WHERE `id_anexo` = '{id_anexo}';")
        conexion.commit()
        # Obtener el número de filas afectadas
        num_filas_afectadas = cursor.rowcount
        print(f"Número de filas afectadas: {num_filas_afectadas}")

    except Exception as e:
        print(f"Error al borrar el anexo SQL: {e}")

    finally:
        cursor.close()



def borrar_proveedor(id):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    
    try:
        cursor.execute(f"DELETE FROM `proveedores` WHERE `id_proveedor` = '{id}';")
        conexion.commit()
        # Obtener el número de filas afectadas
        num_filas_afectadas = cursor.rowcount
        print(f"Número de filas afectadas: {num_filas_afectadas}")
        return True

    except Exception as e:
        print(f"Error al borrar el archivo SQL: {e}")
        return False

    finally:
        cursor.close()


def mover_archivoA(id,ruta_completa):

    sqlUsuario = buscarUsuario(id)
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == 'JEFE'or usuarioO.roll == 'CONTROL':
            ruta_carpeta = '\\aprobados'
            carpetaDatos = "\\datos\\beta"
            ruta = current_dir + carpetaDatos +ruta_carpeta
        try:
            nombre_archivo, extension = os.path.splitext(os.path.basename(ruta_completa))
            
            unaRuta = codificar(ruta_completa)
            otraRuta = codificar(ruta+"\\"+nombre_archivo+extension)
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute(f"UPDATE `archivos` SET `ruta` = '{otraRuta}', `estado` = 'APROBADO', `usuario` = '{usuarioO.id}', `aprobado_por` = '{usuarioO.nombre} {usuarioO.apellido}' WHERE `archivos`.`ruta` = '{unaRuta}';")
            conexion.commit()

            shutil.move(ruta_completa, ruta)
            print(f"El archivo en {ruta_completa} ha sido aprobado.")
        
        except OSError as e:
            print(f"Error al aprobar el archivo en {ruta_completa}: {e}")
    
def mover_archivoNo(id,ruta_completa):
    sqlUsuario = buscarUsuario(id)
    print('string:'+str(sqlUsuario))
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == 'JEFE' or usuarioO.roll == 'CONTROL':
            ruta_carpeta = '\\repositorio'
            carpetaDatos = "\\datos\\beta"
            ruta = current_dir + carpetaDatos +ruta_carpeta
        if usuarioO.roll == 'PROVEEDORES':
            ruta_carpeta = '\\liberados'
            carpetaDatos = "\\datos\\beta"
            ruta = current_dir + carpetaDatos +ruta_carpeta
        try:
            nombre_archivo, extension = os.path.splitext(os.path.basename(ruta_completa))
            unaRuta = codificar(ruta_completa)
            otraRuta = codificar(ruta+"\\"+nombre_archivo+extension)
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute(f"UPDATE `archivos` SET `ruta` = '{otraRuta}' , `estado` = 'NO_APROBADO', `usuario` = '{usuarioO.id}' WHERE `archivos`.`ruta` = '{unaRuta}';")
            conexion.commit()
            shutil.move(ruta_completa, ruta)

            print(f"El archivo en {ruta_completa} ha sido recuperado.")
        
        except OSError as e:
            print(f"Error al Recuperar el archivo en {ruta_completa}: {e}")

@app.route('/')
def mostrar_login():

    return render_template('login.html')

def mover_archivo_Liberar(id,ruta_completa, destino):

    sqlUsuario = buscarUsuario(id)
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == 'CONTROL'or usuarioO.roll == 'PROVEEDORES':
            ruta_carpeta = '\\liberados'
            carpetaDatos = "\\datos\\beta"
            ruta = current_dir + carpetaDatos +ruta_carpeta
        try:
            nombre_archivo, extension = os.path.splitext(os.path.basename(ruta_completa))
            
            unaRuta = codificar(ruta_completa)
            otraRuta = codificar(ruta+"\\"+nombre_archivo+extension)
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute(f"UPDATE `archivos` SET `ruta` = '{otraRuta}', `estado` = 'LIBERADO', `usuario` = '{usuarioO.id}', `destino` = '{destino}' WHERE `archivos`.`ruta` = '{unaRuta}';")
            conexion.commit()

            shutil.move(ruta_completa, ruta)
            print(f"El archivo en {ruta_completa} ha sido LIBERADO.")
        
        except OSError as e:
            print(f"Error al aprobar el archivo en {ruta_completa}: {e}")


@app.route('/usuarios', methods=['POST'])
def usuariosForm():
    usuario = request.form['usuario']
    password = request.form['contrasenia']
    usuario = buscarUsuarioPass(usuario, password)
    usuarioO = Usuario(usuario[0][0],usuario[0][1],usuario[0][2],usuario[0][3],usuario[0][4],usuario[0][5],usuario[0][6],usuario[0][7])
    centro = usuario[0][4]
    conexion = mysql.connect()
    cursor = conexion.cursor()
    if usuarioO.roll == "ADMIN":
        cursor.execute(f"SELECT * FROM `usuarios`;")
    else:
        cursor.execute(f"SELECT * FROM `usuarios` where `centro` = '{centro}';")
    usuarios = cursor.fetchall()
    conexion.commit()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `centro` order by 'detalle';")
    centro = cursor.fetchall()
    conexion.commit()
    
    return render_template('usuarios.html', usuarios = usuarios, centros = centro,usuario = usuarioO)

def usuariosPorID(id_usuario):
    
    usuario = buscarUsuario(id_usuario)
    usuarioO = Usuario(usuario[0][0],usuario[0][1],usuario[0][2],usuario[0][3],usuario[0][4],usuario[0][5],usuario[0][6],usuario[0][7])
    centro = usuario[0][4]
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `centro` = '{centro}';")
    usuarios = cursor.fetchall()
    conexion.commit()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `centro` order by 'detalle';")
    centro = cursor.fetchall()
    conexion.commit()
    
    return render_template('usuarios.html', usuarios = usuarios, centros = centro,usuario = usuarioO)


@app.route('/centro')
def centrosForm():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `centro`;")
    centros = cursor.fetchall()
    conexion.commit()
    
    return render_template('centro.html', centros = centros)

@app.route('/proveedores' , methods=['POST'])
def proveedoresForm():
    centros = buscarCentros()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `proveedores`;")
    proveedores = cursor.fetchall()
    conexion.commit()
    try:
        usuario = request.form['usuario']
       
        password = request.form['contrasenia']
        
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        return render_template('proveedoresM.html', proveedores = proveedores,usuario = usuarioO, repositorio = carpetaRepositorio, id = usuarioO.id,centros = centros)

@app.route('/proveedoresR' , methods=['POST'])
def proveedoresFormR():
    centros = buscarCentros()
    usuario = request.form['usuario']
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `recientes` where id_usuario = {usuario};")
    print("Request: "+usuario)
    proveedoresR = cursor.fetchall()
    conexion.commit()
    sqlUsuario = buscarUsuario(usuario)
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        return render_template('proveedoresR.html', proveedores = proveedoresR,usuario = usuarioO, repositorio = carpetaRepositorio, id = usuarioO.id,centros = centros)

@app.route('/proveedoresDuplicados')
def proveedoresFormD():
    centros = buscarCentros()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `proveedores`;")
    proveedores = cursor.fetchall()
    conexion.commit()

    proveedoresd = buscar_duplicados(proveedores)
    sqlUsuario = buscarUsuario(1)
    """
    try:
        usuario = request.form['usuario']
        print(usuario)
        password = request.form['contrasenia']
        print(password)
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')
    """
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        return render_template('proveedoresDuplicados.html', proveedores = proveedoresd,usuario = usuarioO, repositorio = carpetaRepositorio, id = usuarioO.id,centros = centros)                  


@app.route('/proveedoresDuplicadosBorrar')
def proveedoresFormDe():
    centros = buscarCentros()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `proveedores`;")
    proveedores = cursor.fetchall()
    conexion.commit()

    buscar_duplicados_y_borrar(proveedores)
    sqlUsuario = buscarUsuario(1)
    """
    try:
        usuario = request.form['usuario']
        print(usuario)
        password = request.form['contrasenia']
        print(password)
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')
    """
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        return render_template('proveedoresDuplicados.html', proveedores = proveedores,usuario = usuarioO, repositorio = carpetaRepositorio, id = usuarioO.id,centros = centros)                  

@app.route('/eliminarProveedor' , methods=['POST'])
def eliminarP():
    
    id_proveedor = request.form['id_proveedor']
    pudo = borrar_proveedor(id_proveedor)
    print("Borro?: "+str(pudo))
    centros = buscarCentros()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `proveedores`;")
    proveedores = cursor.fetchall()
    conexion.commit()
    id = request.form['id']
    sqlUsuario = buscarUsuario(id)
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if pudo:
            flash("Se elimino el proveedor correctamente.")
        else:
            flash("El proveedor no se encontró o ya fue eliminado.")
        return render_template('proveedoresM.html', proveedores = proveedores,usuario = usuarioO, repositorio = carpetaRepositorio, id = usuarioO.id,centros = centros)    
"""
@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    
    nombre = request.form['nombre'].capitalize()
    apellido = request.form['apellido'].capitalize()
    sector = request.form['sector']
    centro = request.form['centro']
    mail = request.form['mail'].lower()
    contrasenia = request.form['contrasenia'].replace("\n","")
    roll = request.form['roll'].upper()
    usuarioO = Usuario("",nombre,apellido,sector,centro,mail,contrasenia,roll)
    print(usuarioO.id)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlUsuario = f"INSERT INTO `usuarios` (`id`, `nombre`, `apellido`, `sector`, `centro`, `mail`, `contrasenia`, `roll`) VALUES (NULL, '{usuarioO.nombre}', '{usuarioO.apellido}', '{usuarioO.sector}', '{usuarioO.centro}', '{usuarioO.mail}', '{usuarioO.contraseña}', '{usuarioO.roll}');"
    cursor.execute(sqlUsuario)
    conexion.commit()
    #busqueda de usuario para devolver su perfil de usuario.
    usuario = request.form['usuarioM']
    password = request.form['contraseniaM']

    usuario = buscarUsuarioPass(usuario, password)
    
    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `centro` = '{centro}';")
    usuarios = cursor.fetchall()
    conexion.commit()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `centro` order by 'detalle';")
    centro = cursor.fetchall()
    conexion.commit()
    
    return render_template('usuarios.html', usuarios = usuarios, centros = centro,usuario = usuarioO)
"""
@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    # Datos del nuevo usuario a agregar
    nombre = request.form['nombre'].capitalize()
    apellido = request.form['apellido'].capitalize()
    sector = request.form['sector']
    centro = request.form['centro']
    mail = request.form['mail'].lower()
    contrasenia = request.form['contrasenia'].strip()
    roll = request.form['roll'].upper()
    
    # Crear objeto Usuario para el nuevo usuario
    nuevo_usuario = Usuario("", nombre, apellido, sector, centro, mail, contrasenia, roll)

    # Conexión para insertar el nuevo usuario
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlUsuario = (
        "INSERT INTO `usuarios` (`id`, `nombre`, `apellido`, `sector`, `centro`, `mail`, `contrasenia`, `roll`) "
        f"VALUES (NULL, '{nuevo_usuario.nombre}', '{nuevo_usuario.apellido}', "
        f"'{nuevo_usuario.sector}', '{nuevo_usuario.centro}', '{nuevo_usuario.mail}', "
        f"'{nuevo_usuario.contraseña}', '{nuevo_usuario.roll}');"
    )
    cursor.execute(sqlUsuario)
    conexion.commit()

    # Autenticación del usuario original (que ya estaba logueado)
    usuario = request.form['usuarioM']
    password = request.form['contraseniaM']
    usuario_autenticado = buscarUsuarioPass(usuario, password)

    # Crear objeto Usuario para el usuario autenticado original
    usuarioO = Usuario(
        usuario_autenticado[0][0], usuario_autenticado[0][1], usuario_autenticado[0][2],
        usuario_autenticado[0][3], usuario_autenticado[0][4], usuario_autenticado[0][5],
        usuario_autenticado[0][6], usuario_autenticado[0][7]
    )

    # Recuperar lista de usuarios por el mismo centro
    cursor.execute(f"SELECT * FROM `usuarios` WHERE `centro` = '{usuarioO.centro}';")
    usuarios = cursor.fetchall()

    # Recuperar lista de centros
    cursor.execute("SELECT * FROM `centro` ORDER BY `detalle`;")
    centros = cursor.fetchall()
    conexion.commit()

    # Renderizar la plantilla con los mismos datos originales
    return render_template('usuarios.html', usuarios=usuarios, centros=centros, usuario=usuarioO)

@app.route('/eliminarUsuario', methods=['POST'])
def eliminar_usuario():
    id_usuario = request.form['id']
    # Conexión a la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()
    # Eliminación segura usando parámetros
    sql_eliminar = "DELETE FROM `usuarios` WHERE `id` = %s;"
    cursor.execute(sql_eliminar, (id_usuario,))
    conexion.commit()
    flash("Se elimino el usuario correctamente.")
    idPerfil = request.form['id_perfil']
    usuario = buscarUsuario(idPerfil)
    usuarioO = Usuario(usuario[0][0],usuario[0][1],usuario[0][2],usuario[0][3],usuario[0][4],usuario[0][5],usuario[0][6],usuario[0][7])
    centro = usuario[0][4]
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `centro` = '{centro}';")
    usuarios = cursor.fetchall()
    conexion.commit()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `centro` order by 'detalle';")
    centro = cursor.fetchall()
    conexion.commit()
    
    return render_template('usuarios.html', usuarios = usuarios, centros = centro,usuario = usuarioO)


@app.route('/agregar_centro', methods=['POST'])
def agregar_centro():
    cod = request.form['cod'].capitalize()
    detalle = request.form['detalle'].capitalize()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlUsuario = f"INSERT INTO `centro` (`id_centro`, `cod`, `detalle`) VALUES (NULL, '{cod}', '{detalle}');"
    cursor.execute(sqlUsuario)
    conexion.commit()
    return redirect('/centro')

def buscarProveedor(cuit):
    encontrado = True
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `proveedores` where `cuit`= '{cuit}';")
    proveedores = cursor.fetchall()
    conexion.commit()
    print(len(proveedores))
    if len(proveedores)>0:
        print("Cantidad de registros: "+str(len(proveedores)))
        encontrado = False
    return encontrado

def buscarProveedorReciente(cuit):
    encontrado = False
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `recientes` where `cuit`= '{cuit}';")
    proveedores = cursor.fetchall()
    conexion.commit()
    print(len(proveedores))
    if len(proveedores)>0:
        print("Cantidad de registros: "+str(len(proveedores)))
        encontrado = True
    return encontrado

def verificarCuit(cuit):
    # validaciones minimas
    if len(cuit) != 13 or cuit[2] != "-" or cuit[11] != "-":
        return False

    base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    cuit = cuit.replace("-", "")  # remuevo las barras

    # calculo el digito verificador:
    aux = 0
    for i in range(10):
        aux += int(cuit[i]) * base[i]

    aux = 11 - (aux - (int(aux / 11) * 11))
    if aux == 11:
        aux = 0
    if aux == 10:
        aux = 9

    return aux == int(cuit[10])


def agregar_proveedor_reciente(cuit,detalle,usuario):
    
    cuit = cuit.replace("-","")
    cuit = cuit.replace(" ","")
    cuit = cuit[:2]+"-"+cuit[2:10]+"-"+cuit[-1]
    
    if(buscarProveedorReciente(cuit) == False):
        conexion = mysql.connect()
        cursor = conexion.cursor()
        sqlUsuario = f"INSERT INTO `recientes` (`id_proveedor`, `cuit`, `detalle`, `id_usuario`) VALUES (NULL, '{cuit}', '{detalle}', {usuario});"
        cursor.execute(sqlUsuario)
        conexion.commit()
    print("Se agrego reciente?"+str(buscarProveedorReciente(cuit)))


@app.route('/agregar_proveedor', methods=['POST'])
def agregar_proveedor():
    
    cuit = request.form['cuit']
    cuit = cuit.replace("-","")
    cuit = cuit.replace(" ","")
    cuit = cuit[:2]+"-"+cuit[2:10]+"-"+cuit[-1]
    detalle = request.form['detalleP'].upper()
    existe = buscarProveedor(cuit)
    print(existe)
    if verificarCuit(cuit):
        if existe:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            sqlUsuario = f"INSERT INTO `proveedores` (`id_proveedor`, `cuit`, `detalle`) VALUES (NULL, '{cuit}', '{detalle}');"
            cursor.execute(sqlUsuario)
            conexion.commit()
            flash("Se cargo el proveedor correctamente!")
        else:
            flash("No se pudo cargar el proveedor, cuit ya cargado!")
    else:
        flash("El CUIT no es válido!")
    centros = buscarCentros()
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `proveedores`;")
    proveedores = cursor.fetchall()
    conexion.commit()
    try:
        usuario = request.form['usuario']
        
        password = request.form['contrasenia']
        
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    
    return render_template('proveedoresM.html', proveedores = proveedores,usuario = usuarioO, repositorio = carpetaRepositorio, id = usuarioO.id,centros = centros)
    


@app.route('/repositorio', methods=['GET','POST'])
def verificarUsuario():
    centros = buscarCentros()
    proveedores = buscarProveedores()
    try:
        usuario = request.form['usuario']
       
        password = request.form['contrasenia']
       
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')

    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == "ADMIN":
            return render_template('repo.html',usuario = usuarioO,id=usuarioO.id, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
        
        if usuarioO.centro != "O510" and (usuarioO.roll == "EMPLEADO" or usuarioO.roll == "JEFE") :
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarArchivosApro(usuarioO.centro)
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            print("Repo")
            return render_template('repo.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
        if usuarioO.centro == "O510": #ANTES ERA CONTROL
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarAprovadosControl()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            print("Control")
            return render_template('aprobados.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
        if usuarioO.roll == "PROVEEDORES":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosP()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            print("Proveedores")
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
        if usuarioO.roll == "SERVICIOS":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosS()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            print("Servicios")
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)  
        if usuarioO.roll == "DIRECTO":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosD()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            print("Directo")
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
        if usuarioO.roll == "IMPUESTOS":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosI()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            print("Impuestos")
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)            
    else:
                flash('Error.')
    return redirect('/')

@app.route('/subirAP', methods=['GET','POST'])
def subirAP():
    idP = request.form['id_proveedor']
    print(idP)
    centros = buscarCentros()
    proveedores = buscarProveedoresId(idP)
    
    try:
        id = request.form['id']
        sqlUsuario = buscarUsuario(id)
    except:
        print("Voy por aca")
        return redirect('/noLogin')

    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    
    return render_template('subirProveedor.html',usuario = usuarioO,id=usuarioO.id, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)    

@app.route('/subirAPr', methods=['GET','POST'])
def subirAPr():
    idP = request.form['id_proveedor']
    print("reciente: "+idP)
    centros = buscarCentros()
    proveedores = buscarProveedoresRecientesId(idP)
    
    try:
        id = request.form['id']
        sqlUsuario = buscarUsuario(id)
    except:
        print("Voy por aca")
        return redirect('/noLogin')

    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    
    return render_template('subirProveedor.html',usuario = usuarioO,id=usuarioO.id, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)          
    
@app.route('/subirAnexo', methods=['GET','POST'])
def subirAnexo():
    id_archivo = request.form['id_archivo']
    print(id_archivo)
    archivo = buscarArchivoId(id_archivo)
    
    try:
        id = request.form['id']
        sqlUsuario = buscarUsuario(id)
    except:
        print("Voy por aca")
        return redirect('/noLogin')

    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    
    return render_template('subirAnexo.html',usuario = usuarioO,id=usuarioO.id, repositorio = carpetaRepositorio, archivo = archivo)   

@app.route('/aprobados', methods=['GET','POST'])
def verificarUsuarioAprobados():
    centros = buscarCentros()
    proveedores = buscarProveedores()
    try:
        
        usuario = request.form['usuario']
        password = request.form['contrasenia']
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == "EMPLEADO" or usuarioO.roll == "JEFE":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarArchivosApro(usuarioO.centro)
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template('aprobados.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
                 
    else:
                flash('Error.')
    return redirect('/')

@app.route('/liberados', methods=['GET','POST'])
def verificarUsuarioLiberado():
    centros = buscarCentros()
    proveedores = buscarProveedores()
    try:
        
        usuario = request.form['usuario']
        password = request.form['contrasenia']
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == "CONTROL" or (usuarioO.roll == "JEFE" and usuarioO.centro == "O510"):
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlLiberados = buscarLiberadosC(usuarioO.id)
            listaArchivos = sqlArchivosRepo
            listaLiberados = sqlLiberados
            return render_template('liberados.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, liberados = listaLiberados, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
          
    else:
                flash('Error.')
    return redirect('/')


@app.route('/liberadosCentro', methods=['GET','POST'])
def verificarUsuarioLiberadoCentro():
    centros = buscarCentros()
    proveedores = buscarProveedores()
    try:
        
        usuario = request.form['usuario']
        password = request.form['contrasenia']
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        sqlLiberados = buscarLiberadosCentro(usuarioO.centro)
        listaLiberados = sqlLiberados
        return render_template('liberadosCentro.html',usuario = usuarioO,id=usuarioO.id, liberados = listaLiberados, repositorio = carpetaRepositorio , centros = centros, proveedores = proveedores)
          
    else:
                flash('Error.')
    return redirect('/')

@app.route('/repositorioC', methods=['GET','POST'])
def verificarUsuarioRepositorio():
    centros = buscarCentros()
    proveedores = buscarProveedores()
    try:
        
        usuario = request.form['usuario']
        password = request.form['contrasenia']
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        print("Voy por aca")
        return redirect('/noLogin')
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == "CONTROL" or (usuarioO.roll == "JEFE" and usuarioO.centro == "O510"):
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            
            listaArchivos = sqlArchivosRepo
            
            return render_template('control.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, repositorio = carpetaRepositorio, centros = centros, proveedores = proveedores)
          
    else:
                flash('Error.')
    return redirect('/')

@app.route('/repositorioSubir', methods=['GET','POST'])
def subirA():

    try:
        usuario = request.form['usuario']
        password = request.form['contrasenia']
        origen = request.form['origen']
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        return redirect('/noLogin')
    

    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:

        if request.method == 'POST' and request.form['proveedor'] != "0":
            cuit, proveedor = request.form['proveedor'].split("@")
            if buscarArchivo(request.form['nro'],cuit) == 0:

                if usuarioO.roll == 'PROVEEDORES':
                    
                    s = subirArchivoProveedores(usuarioO.id,carpetaLiberados ,proveedor ,cuit ,request.form['centro'],request.form['nro'],request.form['fecha'],request.form['detalle'])
                    if s == False:
                        flash("Algo salio mal, no se cargo el archivo o demasiado grande(10mb max)!")
                    if s:
                        agregar_proveedor_reciente(cuit,proveedor,usuarioO.id)
                        
                    
                else:
                    s = subirArchivo(usuarioO.id,carpetaRepositorio ,proveedor ,cuit ,request.form['centro'],request.form['nro'],request.form['fecha'],request.form['detalle'])
                    if s == False:
                        flash("Algo salio mal, no se cargo el archivo o demasiado grande(10mb max)!")
                    if s:
                        
                        agregar_proveedor_reciente(cuit,proveedor,usuarioO.id)
                    #activar mail
                    if usuarioO.roll == "EMPLEADO" and s:
                        asunto = "Notificación de Carga Factura"
                        listaAvisos = listaAvisoEmpleado(usuarioO.centro)
                        for usuarioM in listaAvisos:
                            enviarMail(asunto, usuarioM.mail , "Se ha cargado la factura nº: "+request.form['nro']+" del proveedor: "+request.form['proveedor']+".\nPor el usuario: "+usuarioO.apellido+" "+usuarioO.nombre+"."+"\nhref:'http://"+servidorIp+":5000'")
                    
                        
            else:
                flash('Ya existe un archivo con número de factura: '+request.form['nro']+' del proveedor: '+proveedor+'.\nNo se cargo el archivo!')
        else:
            flash("No se eligio proveedor!.")   
        #return volverInicioOrigen(usuarioO.mail,usuarioO.contraseña,origen)
        return """
                <!DOCTYPE html>
                <html>
                    <head>
                        <title>Se cargo el archivo.</title>
                    </head>
                    <body>
                    <script>
                        // Cierra la ventana después de 3 segundos
                            setTimeout(function() {
                            window.close();
                            }, 1000);
                    </script>
                    </body>
                </html>
                """            
    else:
                flash('Error.')        
    return redirect('/')

@app.route('/repositorioSubirAnexo', methods=['GET','POST'])
def subirAnexoRegistro():
        id_archivo = request.form['id_archivo']
        proveedor = request.form['proveedor']
        print(proveedor)
        cuit = request.form['cuit']
        print(cuit)
        nro = request.form['nro']
        fechaPago = request.form['fechaPago']
        detalle = request.form['detalle']
        subirArchivoAnexo(id_archivo,carpetaRepositorio,proveedor,cuit,nro,fechaPago,detalle)
        #return volverInicioOrigen(usuarioO.mail,usuarioO.contraseña,origen)
        return """
                <!DOCTYPE html>
                <html>
                    <head>
                        <title>Se cargo el archivo.</title>
                    </head>
                    <body>
                    <script>
                        // Cierra la ventana después de 3 segundos
                            setTimeout(function() {
                            window.close();
                            }, 1000);
                    </script>
                    </body>
                </html>
                """

def listaAvisoEmpleado(centro):
    lista = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `centro`='{centro}' AND(`roll`='JEFE')")
    usuarioS = cursor.fetchall()
    conexion.commit()
    for usuario in usuarioS:
        
        lista.append(Usuario(usuario[0],usuario[1],usuario[2],usuario[3],usuario[4],usuario[5],usuario[6],usuario[7]))
    return lista

def listaAvisoJefe():
    lista = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `roll`='CONTROL'")
    usuarioS = cursor.fetchall()
    conexion.commit()
    for usuario in usuarioS:
        lista.append(Usuario(usuario[0],usuario[1],usuario[2],usuario[3],usuario[4],usuario[5],usuario[6],usuario[7]))
    return lista

def listaAvisoControl(destino):
    lista = []
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `roll`='{destino}'")
    usuarioS = cursor.fetchall()
    conexion.commit()
    for usuario in usuarioS:
        lista.append(Usuario(usuario[0],usuario[1],usuario[2],usuario[3],usuario[4],usuario[5],usuario[6],usuario[7]))
    return lista

def codificar(algo):
    codificada = base64.b64encode(algo.encode('utf-8')).decode('utf-8')
    return codificada

def decodificar(codificada):
    decodificada = base64.b64decode(codificada).decode('utf-8')
    return decodificada



def subirArchivo(id_usuario, ruta_repo, proveedor,cuit , centro, nro, fechaFactura, detalle):
    usuarioNombre = buscarUsuario(id_usuario)
    
    subio = False
    # Comprobar si la solicitud de publicación tiene la parte del archivo
    if 'file' not in request.files:
        print('No se cargó ningún archivo')
        return subio
    
    file = request.files['file']

    # Si el usuario no selecciona un archivo
    if file.filename == '':
        print('No se cargó ningún archivo')
        return subio
    
    
    else:
        
        
        filename = secure_filename(file.filename)

        # Agregar el valor de cae como un prefijo al nombre del archivo
        nombre_base, extension = os.path.splitext(filename)
        nuevo_nombre = f"{proveedor}_{nro}{extension}"
        filename = nuevo_nombre

        # Guardar el archivo en la ubicación de destino
        file.save(os.path.join(ruta_repo, filename))
        rutaBd = os.path.join(ruta_repo, filename)
        ruta_codificada = codificar(rutaBd)
        print(f"Archivo guardado con éxito como {filename}")
        subio = True
        # Se redirecciona a la página principal
        conexion = mysql.connect()
        cursor = conexion.cursor()
        fechaActual = datetime.now()
        na = usuarioNombre[0][2]+" "+usuarioNombre[0][1]
        sqlUsuario = f"INSERT INTO `archivos` (`id_archivo`, `ruta`, `fecha`, `usuario`, `proveedor`,`centro`,`nro`,`estado`,`nombre`,`fecha_factura`,`detalle`,`cuit`,`usuario_nombre`) VALUES (NULL, '{ruta_codificada}', '{fechaActual}', '{id_usuario}', '{proveedor}', '{centro}','{nro}','NO_APROBADO','{nuevo_nombre}', '{fechaFactura}', '{detalle}','{cuit}','{na}');"
        cursor.execute(sqlUsuario)
        conexion.commit()
    return subio


def subirArchivoProveedores(id_usuario, ruta_repo, proveedor, cuit, centro, nro, fechaFactura, detalle):
    subio = False
    usuarioNombre = buscarUsuario(id_usuario)
    # Comprobar si la solicitud de publicación tiene la parte del archivo
    if 'file' not in request.files:
        print('No se cargó ningún archivo')
        return subio
    
    file = request.files['file']

    # Si el usuario no selecciona un archivo
    if file.filename == '':
        print('No se cargó ningún archivo')
        return subio
    
    
    else:
        filename = secure_filename(file.filename)

        # Agregar el valor de cae como un prefijo al nombre del archivo
        nombre_base, extension = os.path.splitext(filename)
        nuevo_nombre = f"{proveedor}_{nro}{extension}"
        filename = nuevo_nombre

        # Guardar el archivo en la ubicación de destino
        file.save(os.path.join(ruta_repo, filename))
        rutaBd = os.path.join(ruta_repo, filename)
        ruta_codificada = codificar(rutaBd)
        print(f"Archivo guardado con éxito como {filename}")
        subio = True
        # Se redirecciona a la página principal
        conexion = mysql.connect()
        cursor = conexion.cursor()
        fechaActual = datetime.now()
        na = usuarioNombre[0][2]+" "+usuarioNombre[0][1]
        sqlUsuario = f"INSERT INTO `archivos` (`id_archivo`, `ruta`, `fecha`, `usuario`, `proveedor`,`centro`,`nro`,`estado`,`nombre`,`fecha_factura`, `detalle`, `destino`,`aprobado_por`,`cuit`,`usuario_nombre`) VALUES (NULL, '{ruta_codificada}', '{fechaActual}', '{id_usuario}', '{proveedor}', '{centro}','{nro}','LIBERADO','{nuevo_nombre}', '{fechaFactura}', '{detalle}', 'PROVEEDORES', 'PROVEEDORES', '{cuit}','{na}');"
        cursor.execute(sqlUsuario)
        conexion.commit()
    return subio


def subirArchivoAnexo(id_archivo,ruta_repo, proveedor, cuit, nro, fechaPago, detalle):
    
    # Comprobar si la solicitud de publicación tiene la parte del archivo
    if 'file' not in request.files:
        print('No se cargó ningún archivo')
        return subio
    
    file = request.files['file']

    # Si el usuario no selecciona un archivo
    if file.filename == '':
        print('No se cargó ningún archivo')
        return subio
    else:
        filename = secure_filename(file.filename)

        # Agregar el valor de cae como un prefijo al nombre del archivo
        nombre_base, extension = os.path.splitext(filename)
        nuevo_nombre = f"{proveedor}_{nro}_{nombre_base}_{extension}"
        filename = nuevo_nombre
        
        # Guardar el archivo en la ubicación de destino
        file.save(os.path.join(ruta_repo, filename))
        rutaBd = os.path.join(ruta_repo, filename)
        ruta_codificada = codificar(rutaBd)
        print(f"Archivo guardado con éxito como {filename}")
        subio = True
        # Se redirecciona a la página principal
        conexion = mysql.connect()
        cursor = conexion.cursor()
        fechaActual = datetime.now()
        sqlUsuario = f"INSERT INTO comprobantes (`id_anexo`,`id_archivo`, `cuit`, `proveedor`, `nro_fac`, `ruta`,`fechaPago`,`detalle`,`fecha`) VALUES (NULL, '{id_archivo}', '{cuit}', '{proveedor}', '{nro}', '{ruta_codificada}','{fechaPago}', '{detalle}', '{fechaActual}');"
        cursor.execute(sqlUsuario)
        conexion.commit()

def buscarAnexos(id_archivo):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlUsuario = f"Select * from comprobantes where id_archivo = {id_archivo}"
    cursor.execute(sqlUsuario)
    anexos = cursor.fetchall()
    conexion.commit()
    return anexos


@ app.route('/anexos', methods=['POST'])
def ver_A():
    rutas = []
    id = request.form['id']
    usuario = buscarUsuario(id)
    id_archivo = request.form['id_archivo']
    rutas = buscarAnexos(id_archivo)

    return render_template("anexos.html" , anexos = rutas, usuario = usuario)
    
@ app.route('/verPdf', methods=['POST'])
def ver_pdf():
    id_archivo = request.form['id_archivo']
    ruta = rutaArchivo(id_archivo)

    return send_file(ruta, as_attachment=False)

@ app.route('/verPdfCarga', methods=['POST'])
def ver_pdf_carga():
    
    ruta = "./carga.pdf"

    return send_file(ruta, as_attachment=False)

@ app.route('/verAnexo', methods=['POST'])
def ver_Anexo():
    id_archivo = request.form['id_archivo']
    ruta = rutaArchivoAnexo(id_archivo)
    return send_file(ruta, as_attachment=False)


@app.route('/noAprobar', methods=['POST'])#recuperar archivo
def moverArchivoNoAprobado():
    origen = request.form['origen']
    ruta = request.form['archivo']
    id_usuario = request.form['id']
    
    mover_archivoNo(id_usuario,ruta)
    # Buscar el usuario
    sql_usuario = buscarUsuario(id_usuario)
    usuario = ""
    contrasenia = ""
    if sql_usuario and sql_usuario != "()" and sql_usuario != "[]":
        # Crear el objeto Usuario si se encuentra
        usuario_o = Usuario(sql_usuario[0][0],sql_usuario[0][1], sql_usuario[0][2], sql_usuario[0][3],
                            sql_usuario[0][4], sql_usuario[0][5], sql_usuario[0][6], sql_usuario[0][7])
        
        # Redirigir a la URL "/xepositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicioOrigen(usuario,contrasenia, origen)

@app.route('/liberar', methods=['POST'])
def mover_archivo_a_Liberar():
    # Obtener los parámetros de la solicitud POST
    ruta = request.form['archivo']
    id_usuario = request.form['id']
    destino = request.form['destino']
    origen = request.form['origen']
    id_archivo = request.form['id_archivo']
    archivo = buscarArchivoId(id_archivo)
    # Mover el archivo a la carpeta 'aprobados' del usuario
    mover_archivo_Liberar(id_usuario, ruta, destino)
    #mandar mail a los que correspondan
    
    # Buscar el usuario
    sql_usuario = buscarUsuario(id_usuario)
    usuario = ""
    contrasenia = ""
    if sql_usuario and sql_usuario != "()" and sql_usuario != "[]":
        # Crear el objeto Usuario si se encuentra
        usuario_o = Usuario(sql_usuario[0][0],sql_usuario[0][1], sql_usuario[0][2], sql_usuario[0][3],
                            sql_usuario[0][4], sql_usuario[0][5], sql_usuario[0][6], sql_usuario[0][7])
        
        # Redirigir a la URL "/xepositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
        if usuario_o.roll == "CONTROL":
            listaAvisos = listaAvisoControl(destino)
            asunto = "Notificación de Liberación Factura"
            for usuarioM in listaAvisos:
                mensaje = "Se ha liberado la factura: "+archivo[0][6]+" del proveedor: "+archivo[0][4]+".\nPor el usuario: "+usuario_o.apellido+" "+usuario_o.nombre+"\nCentro: "+usuario_o.centro+"."+"\nhref:'http://"+servidorIp+":5000'"
                enviarMail(asunto, usuarioM.mail , mensaje)
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicioOrigen(usuario,contrasenia,origen)


@app.route('/editarDetalle', methods=['POST'])
def detalle_editar():
    origen = request.form['origen']
    # Obtener los parámetros de la solicitud POST
    id_usuario = request.form['usuario']
    id_archivo = request.form['id_archivo']
    detalle = request.form['detalle']
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sqlUsuario = f"UPDATE `archivos` SET `detalle` = '{detalle}' WHERE `id_archivo` = '{id_archivo}';"
    cursor.execute(sqlUsuario)
    conexion.commit()
    sql_usuario = buscarUsuario(id_usuario)
    usuario = ""
    contrasenia = ""
    if sql_usuario and sql_usuario != "()" and sql_usuario != "[]":
        # Crear el objeto Usuario si se encuentra
        usuario_o = Usuario(sql_usuario[0][0],sql_usuario[0][1], sql_usuario[0][2], sql_usuario[0][3],
                            sql_usuario[0][4], sql_usuario[0][5], sql_usuario[0][6], sql_usuario[0][7])
        
        # Redirigir a la URL "/xepositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicioOrigen(usuario,contrasenia, origen)
    
    

@app.route('/aprobar', methods=['POST'])
def moverArchivoAprobado():
    # Obtener los parámetros de la solicitud POST
    origen = request.form['origen']
    ruta = request.form['archivo']
    id_usuario = request.form['id']
    id_archivo = request.form['id_archivo']
    archivo = buscarArchivoId(id_archivo)
    # Mover el archivo a la carpeta 'aprobados' del usuario
    print(archivo)
    mover_archivoA(id_usuario, ruta)
    
    # Buscar el usuario
    sql_usuario = buscarUsuario(id_usuario)
    usuario = ""
    contrasenia = ""
    if sql_usuario and sql_usuario != "()" and sql_usuario != "[]":
        # Crear el objeto Usuario si se encuentra
        usuario_o = Usuario(sql_usuario[0][0],sql_usuario[0][1], sql_usuario[0][2], sql_usuario[0][3],
                            sql_usuario[0][4], sql_usuario[0][5], sql_usuario[0][6], sql_usuario[0][7])
        
        # Redirigir a la URL "/xepositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
        if usuario_o.roll == "JEFE":
            listaAvisos = listaAvisoJefe()
            asunto = "Notificación de Aprobación Factura."
            for usuarioM in listaAvisos:
                mensaje = "Se ha aprobado la factura: "+archivo[0][6]+" del proveedor: "+archivo[0][4]+".\nPor el usuario: "+usuario_o.apellido+" "+usuario_o.nombre+"\nCentro: "+usuario_o.centro+"."+"\nhref:'http://"+servidorIp+":5000'"
                enviarMail(asunto, usuarioM.mail , mensaje)
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicioOrigen(usuario,contrasenia, origen)

@app.route('/actualizar_estado', methods=['POST'])
def actualizar_estado():
    id_usuario = request.form['id_usuario']
    id_archivo = request.form['id_archivo']
    nuevo_estado = request.form['estado']
    mensajeOk = "Se actualizó correctamente."
    # Aquí deberías realizar la actualización en tu base de datos o en tu sistema de almacenamiento
    print(nuevo_estado)
    if nuevo_estado == "FINALIZADO":
        if len(buscarAnexos(id_archivo))>0:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            sql = f"UPDATE `archivos` SET `estado` = '{nuevo_estado}' WHERE `id_archivo` = '{id_archivo}';"
            cursor.execute(sql)
            conexion.commit()
            flash(mensajeOk)
        else:
            flash("No se puede marcar como 'FINALIZADO', no se adjuntó documento.")
    if nuevo_estado != "FINALIZADO":
        conexion = mysql.connect()
        cursor = conexion.cursor()
        sql = f"UPDATE `archivos` SET `estado` = '{nuevo_estado}' WHERE `id_archivo` = '{id_archivo}';"
        cursor.execute(sql)
        conexion.commit()
        flash(mensajeOk)
    
    sql_usuario = buscarUsuario(id_usuario)
    usuario = ""
    contrasenia = ""
    if sql_usuario and sql_usuario != "()" and sql_usuario != "[]":
        # Crear el objeto Usuario si se encuentra
        usuario_o = Usuario(sql_usuario[0][0],sql_usuario[0][1], sql_usuario[0][2], sql_usuario[0][3],
                            sql_usuario[0][4], sql_usuario[0][5], sql_usuario[0][6], sql_usuario[0][7])
        
        # Redirigir a la URL "/xepositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicioOrigen(usuario,contrasenia, "proveedores")
#-------------------------------------------------------------------------------------------------------
#Se debe modificar la ip que corresponda al equipo en donde se esta corriendo

if __name__ == "__main__":
    app.run(host= servidorIp ,debug=True)
"""
if __name__ == "__main__":
    http_server = WSGIServer((servidorIp, 5000), app)
    http_server.serve_forever()
"""    
        
