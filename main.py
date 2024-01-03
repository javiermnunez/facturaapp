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
# Obtener la ruta al directorio actual del script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Agregar el directorio al sys.path
sys.path.append(current_dir)
carpetaRepositorio = current_dir+"\\datos\\beta\\repositorio"
carpetaAprobados = current_dir+"\\datos\\beta\\aprobados"




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

    return ruta.replace(" ","_")
    

def renombrarArchivo(rutaArchivoOriginal,nombreNuevo):
    # Ruta del archivo actual

    ruta_original = rutaArchivoOriginal

    # Nuevo nombre del archivo
    nuevo_nombre = nombreNuevo

    # Combinar la ruta original con el nuevo nombre
    ruta_nueva = os.path.join(os.path.dirname(ruta_original), nuevo_nombre)

    # Cambiar el nombre del archivo
    os.rename(ruta_original, ruta_nueva)

def volverInicio(usuario, password):
    sqlUsuario = buscarUsuarioPass(usuario,password)
    
    print('string:'+str(sqlUsuario))
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
        
    else:
        usuarioO = None
    
    if usuarioO:
        sqlArchivosRepo = buscarArchivosRepo(usuarioO.centro)
        sqlArchivosApro = buscarArchivosApro(usuarioO.centro)
        listaArchivos = sqlArchivosRepo
        listaArchivosA = sqlArchivosApro
        return render_template('index.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)           
    else:
                flash('Error.')
    return redirect('/')


def buscarArchivosRepo(centro):
    print(centro)
    repositorio = []
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM archivos where `centro`='{centro}' AND (estado='NO_APROBADO');")
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
        repositorio.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado])
    
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
        aprobados.append([id,ruta,fecha,usuario,proveedor,centro,cae,estado])

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


#Función para la eliminacion de archivos 
@app.route('/eliminarArchivo', methods=['POST'])
def eliminarArchivo():
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
    return volverInicio(usuario,contrasenia)


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


def mover_archivo(id,ruta_completa):
    sqlUsuario = buscarUsuario(id)
    print('string:'+str(sqlUsuario))
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
        id = sqlUsuario[0][0]
    else:
        usuarioO = None
    
    if usuarioO:
        carpetasEmpleados = []
        ficheros = []
        listaArchivos = []
        listaArchivosA = []
        if usuarioO.roll == 'JEFE':
            ruta_carpeta = '\\repositorio'
            carpetaDatos = "\\datos\\beta"
            ruta = current_dir + carpetaDatos +ruta_carpeta
        try:
            nombre_archivo, extension = os.path.splitext(os.path.basename(ruta_completa))
            unaRuta = codificar(ruta_completa)
            otraRuta = codificar(ruta+"\\"+nombre_archivo+extension)
            cursor = conexion.cursor()
            cursor.execute(f"UPDATE `archivos` SET `ruta` = '{otraRuta}' WHERE `archivos`.`ruta` = '{unaRuta}';")
            conexion.commit()
            shutil.move(ruta_completa, ruta)

            print(f"El archivo en {ruta_completa} ha sido recuperado.")
        
        except OSError as e:
            print(f"Error al eliminar el archivo en {ruta_completa}: {e}")
    rutaEmpleados = current_dir + carpetaDatos + ruta_carpeta
    rutaAprobados = current_dir+carpetaDatos+'\\aprobados'
    
    with os.scandir(rutaEmpleados) as empleados:
        for carpeta in empleados:
            carpetasEmpleados.append(carpeta.path)

            with os.scandir(carpeta.path) as repositorios:
                for repositorio in repositorios:
                    if repositorio.is_file():
                        ficheros.append(repositorio.name)
                        listaArchivos.append([carpeta.path, repositorio.name])
    with os.scandir(rutaAprobados) as aprobados:
        for aprobado in aprobados:
            if aprobado.is_file():
                listaArchivosA.append([rutaAprobados,aprobado.name])


    return render_template('index.html', usuario = usuarioO,ficheros = ficheros ,id=id, archivos = listaArchivos, ruta = ruta, archivosA = listaArchivosA) 

def mover_archivoA(id,ruta_completa):

    sqlUsuario = buscarUsuario(id)
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        if usuarioO.roll == 'JEFE':
            ruta_carpeta = '\\aprobados'
            carpetaDatos = "\\datos\\beta"
            ruta = current_dir + carpetaDatos +ruta_carpeta
        try:
            nombre_archivo, extension = os.path.splitext(os.path.basename(ruta_completa))
            nombre = nombre_archivo.replace(" ","_")
            unaRuta = codificar(ruta_completa)
            otraRuta = codificar(ruta+"\\"+nombre+extension)
            cursor = conexion.cursor()
            cursor.execute(f"UPDATE `archivos` SET `ruta` = '{otraRuta}', `estado` = 'APROBADO' WHERE `archivos`.`ruta` = '{unaRuta}';")
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
        if usuarioO.roll == 'JEFE':
            ruta_carpeta = '\\repositorio'
            carpetaDatos = "\\datos\\beta"
            ruta = current_dir + carpetaDatos +ruta_carpeta
        try:
            nombre_archivo, extension = os.path.splitext(os.path.basename(ruta_completa))
            unaRuta = codificar(ruta_completa)
            otraRuta = codificar(ruta+"\\"+nombre_archivo+extension)
            cursor = conexion.cursor()
            cursor.execute(f"UPDATE `archivos` SET `ruta` = '{otraRuta}' , `estado` = 'NO_APROBADO' WHERE `archivos`.`ruta` = '{unaRuta}';")
            conexion.commit()
            shutil.move(ruta_completa, ruta)

            print(f"El archivo en {ruta_completa} ha sido recuperado.")
        
        except OSError as e:
            print(f"Error al Recuperar el archivo en {ruta_completa}: {e}")

@app.route('/')
def mostrar_login():

    return render_template('login.html')


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
    cae = request.form['cae'].lower()
    mail = request.form['mail'].lower()
    contrasenia = request.form['contrasenia'].replace("\n","")
    roll = request.form['roll'].upper()
    usuario = Usuario(nombre,
        apellido,
        sector,
        centro,
        mail,
        contrasenia,
        roll
    )
    cursor = conexion.cursor()
    sqlUsuario = f"INSERT INTO `usuarios` (`id`, `nombre`, `apellido`, `sector`, `centro`, `mail`, `contrasenia`, `roll`) VALUES (NULL, '{usuario.nombre}', '{usuario.apellido}', '{usuario.sector}', '{usuario.centro}', '{usuario.mail}', '{usuario.contraseña}', '{usuario.roll}');"
    cursor.execute(sqlUsuario)
    conexion.commit()
    return redirect('/usuarios')

    
@app.route('/repositorio', methods=['GET','POST'])
def verificarUsuario():
    
    try:
        
        usuario = request.form['usuario']
        password = request.form['contrasenia']
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        return redirect('/noLogin')
    
    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        sqlArchivosRepo = buscarArchivosRepo(usuarioO.centro)
        sqlArchivosApro = buscarArchivosApro(usuarioO.centro)
        listaArchivos = sqlArchivosRepo
        listaArchivosA = sqlArchivosApro
        
        
        return render_template('index.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA, repositorio = carpetaRepositorio)           
    else:
                flash('Error.')
    return redirect('/')

@app.route('/repositorioSubir', methods=['GET','POST'])
def subirA():

    try:
        usuario = request.form['usuario']
        password = request.form['contrasenia']
        sqlUsuario = buscarUsuarioPass(usuario,password)
    except:
        return redirect('/noLogin')
    

    if str(sqlUsuario) != "()" and str(sqlUsuario) != "[]":
        usuarioO = Usuario(sqlUsuario[0][0],sqlUsuario[0][1],sqlUsuario[0][2],sqlUsuario[0][3],sqlUsuario[0][4],sqlUsuario[0][5],sqlUsuario[0][6],sqlUsuario[0][7])
    else:
        usuarioO = None
    
    if usuarioO:
        sqlArchivosRepo = buscarArchivosRepo(usuarioO.id)
        sqlArchivosApro = buscarArchivosApro(usuarioO.id)
        listaArchivos = sqlArchivosRepo
        listaArchivosA = sqlArchivosApro
        
        if request.method == 'POST':
            subirArchivo(usuarioO.id,carpetaRepositorio ,request.form['proveedor'],request.form['centro'],request.form['cae'])
        render_template('index.html',usuario = usuarioO,id=usuarioO.id, archivos = listaArchivos, archivosA = listaArchivosA)
        return redirect('/repositorio')            
    else:
                flash('Error.')        
    return redirect('/')

def codificar(algo):
    codificada = base64.b64encode(algo.encode('utf-8')).decode('utf-8')
    return codificada

def decodificar(codificada):
    decodificada = base64.b64decode(codificada).decode('utf-8')
    return decodificada

def subirArchivo(id_usuario, ruta_repo, proveedor,centro,cae):
    #Comprobar si la solicitud de publicación tiene la parte del archivo
    if 'file' not in request.files:
        print('No se cargo ningun archivo')
        return redirect(request.url)
    file = request.files['file']
    #Si el usuario no selecciona un archivo
    if file.filename == '':
        print('No se cargo ningun archivo')
        return redirect(request.url)
    else:
        filename = secure_filename(file.filename)
        file.save(os.path.join(ruta_repo, filename))
        rutaBd = f"{ruta_repo}\\{file.filename}"
        ruta_codificada = codificar(rutaBd)
        print("Archivo guardado con éxito")
        #Se redirecciona a la pagina principal
        cursor = conexion.cursor()
        fechaActual = datetime.now()
        sqlUsuario = f"INSERT INTO `archivos` (`id_archivo`, `ruta`, `fecha`, `usuario`, `proveedor`,`centro`,`cae`,`estado`) VALUES (NULL, '{ruta_codificada}', '{fechaActual}', '{id_usuario}', '{proveedor}', '{centro}','{cae}','NO_APROBADO');"
        cursor.execute(sqlUsuario)
        conexion.commit()
    
@ app.route('/verPdf', methods=['POST'])
def ver_pdf():
    id_archivo = request.form['id_archivo']
    ruta = rutaArchivo(id_archivo)

    return send_file(ruta, as_attachment=False)

@app.route('/noAprobar', methods=['POST'])#recuperar archivo
def moverArchivoNoAprobado():
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
    return volverInicio(usuario,contrasenia)



@app.route('/aprobar', methods=['POST'])
def moverArchivoAprobado():
    # Obtener los parámetros de la solicitud POST
    ruta = request.form['archivo']
    id_usuario = request.form['id']
    # Mover el archivo a la carpeta 'aprobados' del usuario
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
    # Manejar el caso en el que no se encuentra el usuario
    return volverInicio(usuario,contrasenia)

#-------------------------------------------------------------------------------------------------------
#Se debe modificar la ip que corresponda al equipo en donde se esta corriendo
if __name__ == "__main__":
    app.run(host='89.0.0.28')
