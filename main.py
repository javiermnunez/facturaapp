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
from clases.Usuario import Usuario
from clases.Centro import Centro
from clases.Estado import Estado
from clases.Roll import Roll
import mysql.connector #nuevo
from datetime import datetime
from email.message import EmailMessage
import ssl
import smtplib

servidorIp = "89.0.0.28"

# Obtener la ruta al directorio actual del script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Agregar el directorio al sys.path
sys.path.append(current_dir)
carpetaRepositorio = current_dir+"\\datos\\beta\\repositorio"
carpetaAprobados = current_dir+"\\datos\\beta\\aprobados"
carpetaLiberados = current_dir+"\\datos\\beta\\liberados"

def enviarMail(destinatario, mensaje):
    try:
        em = EmailMessage()
        em["To"] = destinatario
        em["Subject"] = "Se cargó una nueva Factura."
        em.set_content(mensaje)
        
        with smtplib.SMTP("mail.laboratoriosbeta.com.ar", 26) as smtp:
            smtp.login("sistemas@laboratoriosbeta.com.ar", "Sanjuan2266")
            smtp.sendmail("sistemas@laboratoriosbeta.com.ar", destinatario, em.as_string())
            return True
    except Exception as e:
        return (f"Error al enviar el correo: {e}")
        


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

#Declaración  de variable que hace referencia a la carpeta contenedora para alojar los archivos
FILE_CONTAINER = './cont/'

app = Flask(__name__, template_folder='templates')
app.debug = True
app.config['FILE_CONTAINER'] = FILE_CONTAINER
app.secret_key = "vigoray"
conexion = mysql.connector.connect(host="localhost", user="root", passwd="",database="personas") #nuevo

def rutaArchivo(id_archivo):
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
    
def buscarArchivoId(id_archivo):
    cursor = conexion.cursor()
    sqlArchivo = f"select * from archivos where id_archivo = {id_archivo};"
    cursor.execute(sqlArchivo)
    archivo = cursor.fetchall()
    conexion.commit()
    return archivo

def buscarArchivo(nro,proveedor):
    salida = 1
    print("numero "+nro)
    print("proveedor "+proveedor)
    cursor = conexion.cursor()
    sqlArchivo = f"select * from archivos where `nro` = {nro} AND `proveedor` = '{proveedor}'"
    cursor.execute(sqlArchivo)
    archivo = cursor.fetchall()
    conexion.commit()
    print(len(archivo))
    if len(archivo) == 0:
        salida = 0
    return salida

def buscarArchivoPorRuta(ruta):
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
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,aprobado])

    return aprobadosC

def buscarLiberadosP():
    aprobadosC = []
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM archivos WHERE (estado='LIBERADO' OR estado='PAGADO') AND destino='PROVEEDORES';")
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
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle])

    return aprobadosC

def buscarLiberadosS():
    aprobadosC = []
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos where estado='LIBERADO' AND(destino='SERVICIOS');")
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
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle])

    return aprobadosC

def buscarLiberadosD():
    aprobadosC = []
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos where estado='LIBERADO' AND(destino='DIRECTO');")
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
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle])

    return aprobadosC

def buscarLiberadosC(idU):
    aprobadosC = []
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos where estado='LIBERADO' AND(usuario='{idU}');")
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
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,liberado])

    return aprobadosC

def buscarLiberadosCentro(centro):

    aprobadosC = []
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos WHERE (estado='LIBERADO' OR estado='PAGADO') AND(centro='{centro}');")
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
        aprobadosC.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,liberado])

    return aprobadosC


def volverInicioOrigen(usuario, password,origen):
    sqlUsuario = buscarUsuarioPass(usuario,password)
    
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
            return render_template(f'{origen}.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)
        if usuarioO.roll == "CONTROL":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarAprovadosControl()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            if origen == "liberados":
                sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
                sqlLiberados = buscarLiberadosC(usuarioO.id)
                listaArchivos = sqlArchivosRepo
                listaLiberados = sqlLiberados
                return render_template('liberados.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, liberados = listaLiberados, repositorio = carpetaRepositorio)
            return render_template(f'{origen}.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)   
        if usuarioO.roll == "PROVEEDORES":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosP()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)
        if usuarioO.roll == "SERVICIOS":
            sqlArchivosApro = buscarLiberadosS()
          
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)   
        if usuarioO.roll == "DIRECTO":
            sqlArchivosApro = buscarLiberadosD()
            
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)         
    else:
                flash('Error.')
    return redirect('/')

def buscarArchivosRepo(usuario,centro):
    print(centro)
    repositorio = []
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
        
        repositorio.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle])
    
    return repositorio

def buscarArchivosApro(centro):
    aprobados = []
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
        aprobados.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado,nombre,fechaFC,detalle,aprobado])

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
    <h1>Debes iniciar sesión.</h1>
    <a class="btn btn-primary" href="/">Volver</a>
    </div>
    </div>
     </body> """

@app.route('/mail')
def mail():
    
    resultado = enviarMail("jmn@betalab.com.ar", "Hola, este es el mensaje.")
        
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
        
        # Redirigir a la URL "/repositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
    # Manejar el caso en el que no se encuentra el usuario
    redirect('/repositorio')
    return volverInicioOrigen(usuario,contrasenia,origen)


#Funcion para la descarga de archivos
@app.route('/download_file/<filename>')
def return_files_tut(filename):
    file_path = FILE_CONTAINER + filename
    print(file_path)
    return send_file(file_path, as_attachment=True, attachment_filename='')
#-------------------------------------------------------------------------------------------------------
def buscarUsuario(id): #nuevo
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `id`={id}")
    usuario = cursor.fetchall()
    conexion.commit()
    
    return usuario

def buscarUsuarioPass(usuario,contrasenia): #nuevo
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where mail='{usuario}' AND (contrasenia='{contrasenia}')")
    usuario = cursor.fetchall()
    print(usuario)
    conexion.commit()
    
    return usuario
def borrar_archivo(ruta_completa):
    try:
        os.remove(ruta_completa)
        borrar_archivo_SQL(ruta_completa)
        print(f"El archivo en {ruta_completa} ha sido eliminado exitosamente.")
        
    except OSError as e:
        print(f"Error al eliminar el archivo en {ruta_completa}: {e}")

def borrar_archivo_SQL(ruta):
    unaRuta = codificar(ruta)
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
            cursor = conexion.cursor()
            cursor.execute(f"UPDATE `archivos` SET `ruta` = '{otraRuta}', `estado` = 'LIBERADO', `usuario` = '{usuarioO.id}', `destino` = '{destino}' WHERE `archivos`.`ruta` = '{unaRuta}';")
            conexion.commit()

            shutil.move(ruta_completa, ruta)
            print(f"El archivo en {ruta_completa} ha sido LIBERADO.")
        
        except OSError as e:
            print(f"Error al aprobar el archivo en {ruta_completa}: {e}")


@app.route('/usuarios')
def usuariosForm():
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `usuarios`;")
    usuarios = cursor.fetchall()
    conexion.commit()
    
    return render_template('usuarios.html', usuarios = usuarios)

@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    nombre = request.form['nombre'].capitalize()
    apellido = request.form['apellido'].capitalize()
    sector = request.form['sector'].lower()
    centro = request.form['centro'].upper()
    mail = request.form['mail'].lower()
    contrasenia = request.form['contrasenia'].replace("\n","")
    roll = request.form['roll'].upper()
    usuario = Usuario("",nombre,apellido,sector,centro,mail,contrasenia,roll)
    cursor = conexion.cursor()
    sqlUsuario = f"INSERT INTO `usuarios` (`id`, `nombre`, `apellido`, `sector`, `centro`, `mail`, `contrasenia`, `roll`) VALUES (NULL, '{usuario.nombre}', '{usuario.apellido}', '{usuario.sector}', '{usuario.centro}', '{usuario.mail}', '{usuario.contraseña}', '{usuario.roll}');"
    cursor.execute(sqlUsuario)
    conexion.commit()
    return redirect('/usuarios')




@app.route('/repositorio', methods=['GET','POST'])
def verificarUsuario():
    try:
        usuario = request.form['usuario']
        print(usuario)
        password = request.form['contrasenia']
        print(password)
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
            return render_template('repo.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)
        if usuarioO.roll == "CONTROL":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarAprovadosControl()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template('aprobados.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)
        if usuarioO.roll == "PROVEEDORES":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosP()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)
        if usuarioO.roll == "SERVICIOS":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosS()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)  
        if usuarioO.roll == "DIRECTO":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlArchivosApro = buscarLiberadosD()
            listaArchivos = sqlArchivosRepo
            listaArchivosA = sqlArchivosApro
            return render_template('proveedores.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)            
    else:
                flash('Error.')
    return redirect('/')

@app.route('/aprobados', methods=['GET','POST'])
def verificarUsuarioAprobados():
    
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
            return render_template('aprobados.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)
                 
    else:
                flash('Error.')
    return redirect('/')

@app.route('/liberados', methods=['GET','POST'])
def verificarUsuarioLiberado():
    
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
        if usuarioO.roll == "CONTROL":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            sqlLiberados = buscarLiberadosC(usuarioO.id)
            listaArchivos = sqlArchivosRepo
            listaLiberados = sqlLiberados
            return render_template('liberados.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, liberados = listaLiberados, repositorio = carpetaRepositorio)
          
    else:
                flash('Error.')
    return redirect('/')


@app.route('/liberadosCentro', methods=['GET','POST'])
def verificarUsuarioLiberadoCentro():
    
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
        return render_template('liberadosCentro.html',usuario = usuarioO,id=usuarioO.id, liberados = listaLiberados, repositorio = carpetaRepositorio)
          
    else:
                flash('Error.')
    return redirect('/')

@app.route('/repositorioC', methods=['GET','POST'])
def verificarUsuarioRepositorio():
    
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
        if usuarioO.roll == "CONTROL":
            sqlArchivosRepo = buscarArchivosRepo(usuarioO, usuarioO.centro)
            
            listaArchivos = sqlArchivosRepo
            
            return render_template('control.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, repositorio = carpetaRepositorio)
          
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

        if request.method == 'POST':
            if buscarArchivo(request.form['nro'],request.form['proveedor']) == 0:

                if usuarioO.roll == 'PROVEEDORES':
                    
                    s = subirArchivoProveedores(usuarioO.id,carpetaLiberados ,request.form['proveedor'],request.form['centro'],request.form['nro'],request.form['fecha'],request.form['detalle'])
                    if s == False:
                        flash("Algo salio mal, no se cargo el archivo!")
                    
                        
                    
                else:
                    s = subirArchivo(usuarioO.id,carpetaRepositorio ,request.form['proveedor'],request.form['centro'],request.form['nro'],request.form['fecha'],request.form['detalle'])
                    if s == False:
                        flash("Algo salio mal, no se cargo el archivo!")
                    #activar mail
                    if usuarioO.roll == "EMPLEADO" and s:
                        listaAvisos = listaAvisoEmpleado(usuarioO.centro)
                        for usuarioM in listaAvisos:
                            enviarMail(usuarioM.mail , "Se ha subido la factura: "+request.form['nro']+" del proveedor: "+request.form['proveedor']+".\nPor el usuario: "+usuarioO.apellido+" "+usuarioO.nombre+"."+"\nhref:'http://"+servidorIp+":5000'")
                    
                        
            else:
                flash('Ya existe un archivo con número de factura: '+request.form['nro']+' del proveedor: '+request.form['proveedor']+'.\nNo se cargo el archivo!')
           
        return volverInicioOrigen(usuarioO.mail,usuarioO.contraseña,origen)            
    else:
                flash('Error.')        
    return redirect('/')

def listaAvisoEmpleado(centro):
    lista = []
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `centro`='{centro}' AND(`roll`='JEFE')")
    usuarioS = cursor.fetchall()
    conexion.commit()
    for usuario in usuarioS:
        
        lista.append(Usuario(usuario[0],usuario[1],usuario[2],usuario[3],usuario[4],usuario[5],usuario[6],usuario[7]))
    return lista

def listaAvisoJefe():
    lista = []
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM `usuarios` where `roll`='CONTROL'")
    usuarioS = cursor.fetchall()
    conexion.commit()
    for usuario in usuarioS:
        lista.append(Usuario(usuario[0],usuario[1],usuario[2],usuario[3],usuario[4],usuario[5],usuario[6],usuario[7]))
    return lista

def listaAvisoControl(destino):
    lista = []
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



def subirArchivo(id_usuario, ruta_repo, proveedor, centro, nro, fechaFactura, detalle):
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
        cursor = conexion.cursor()
        fechaActual = datetime.now()
        sqlUsuario = f"INSERT INTO `archivos` (`id_archivo`, `ruta`, `fecha`, `usuario`, `proveedor`,`centro`,`nro`,`estado`,`nombre`,`fecha_factura`,`detalle`) VALUES (NULL, '{ruta_codificada}', '{fechaActual}', '{id_usuario}', '{proveedor}', '{centro}','{nro}','NO_APROBADO','{nuevo_nombre}', '{fechaFactura}', '{detalle}');"
        cursor.execute(sqlUsuario)
        conexion.commit()
    return subio


def subirArchivoProveedores(id_usuario, ruta_repo, proveedor, centro, nro, fechaFactura, detalle):
    subio = False
    # Comprobar si la solicitud de publicación tiene la parte del archivo
    if 'file' not in request.files:
        print('No se cargó ningún archivo')
        return redirect(request.url)
    
    file = request.files['file']

    # Si el usuario no selecciona un archivo
    if file.filename == '':
        print('No se cargó ningún archivo')
        return redirect(request.url)
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
        cursor = conexion.cursor()
        fechaActual = datetime.now()
        sqlUsuario = f"INSERT INTO `archivos` (`id_archivo`, `ruta`, `fecha`, `usuario`, `proveedor`,`centro`,`nro`,`estado`,`nombre`,`fecha_factura`, `detalle`, `destino`) VALUES (NULL, '{ruta_codificada}', '{fechaActual}', '{id_usuario}', '{proveedor}', '{centro}','{nro}','LIBERADO','{nuevo_nombre}', '{fechaFactura}', '{detalle}', 'PROVEEDORES');"
        cursor.execute(sqlUsuario)
        conexion.commit()
    return subio

    
@ app.route('/verPdf', methods=['POST'])
def ver_pdf():
    id_archivo = request.form['id_archivo']
    ruta = rutaArchivo(id_archivo)

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
        
        # Redirigir a la URL "/repositorio" con las credenciales del usuario como parámetros de consulta
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
        
        # Redirigir a la URL "/repositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
        if usuario_o.roll == "CONTROL":
            listaAvisos = listaAvisoControl(destino)
            for usuarioM in listaAvisos:
                mensaje = "Se ha liberado la factura: "+archivo[0][6]+" del proveedor: "+archivo[0][4]+".\nPor el usuario: "+usuario_o.apellido+" "+usuario_o.nombre+"\nCentro: "+usuario_o.centro+"."+"\nhref:'http://"+servidorIp+":5000'"
                enviarMail(usuarioM.mail , mensaje)
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicioOrigen(usuario,contrasenia,origen)


@app.route('/editarDetalle', methods=['POST'])
def detalle_editar():
    origen = request.form['origen']
    # Obtener los parámetros de la solicitud POST
    id_usuario = request.form['usuario']
    id_archivo = request.form['id_archivo']
    detalle = request.form['detalle']
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
        
        # Redirigir a la URL "/repositorio" con las credenciales del usuario como parámetros de consulta
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
        
        # Redirigir a la URL "/repositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
        if usuario_o.roll == "JEFE":
            listaAvisos = listaAvisoJefe()
            for usuarioM in listaAvisos:
                mensaje = "Se ha aprobado la factura: "+archivo[0][6]+" del proveedor: "+archivo[0][4]+".\nPor el usuario: "+usuario_o.apellido+" "+usuario_o.nombre+"\nCentro: "+usuario_o.centro+"."+"\nhref:'http://"+servidorIp+":5000'"
                enviarMail(usuarioM.mail , mensaje)
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicioOrigen(usuario,contrasenia, origen)

@app.route('/actualizar_estado', methods=['POST'])
def actualizar_estado():
    id_usuario = request.form['id_usuario']
    id_archivo = request.form['id_archivo']
    nuevo_estado = request.form['estado']
    # Aquí deberías realizar la actualización en tu base de datos o en tu sistema de almacenamiento
    cursor = conexion.cursor()
    sqlUsuario = f"UPDATE `archivos` SET `estado` = '{nuevo_estado}' WHERE `id_archivo` = '{id_archivo}';"
    cursor.execute(sqlUsuario)
    conexion.commit()
    sql_usuario = buscarUsuario(id_usuario)
    usuario = ""
    contrasenia = ""
    if sql_usuario and sql_usuario != "()" and sql_usuario != "[]":
        # Crear el objeto Usuario si se encuentra
        usuario_o = Usuario(sql_usuario[0][0],sql_usuario[0][1], sql_usuario[0][2], sql_usuario[0][3],
                            sql_usuario[0][4], sql_usuario[0][5], sql_usuario[0][6], sql_usuario[0][7])
        
        # Redirigir a la URL "/repositorio" con las credenciales del usuario como parámetros de consulta
        usuario = usuario_o.mail
        contrasenia = usuario_o.contraseña
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicioOrigen(usuario,contrasenia, "proveedores")
#-------------------------------------------------------------------------------------------------------
#Se debe modificar la ip que corresponda al equipo en donde se esta corriendo
if __name__ == "__main__":
    app.run(host= servidorIp )
