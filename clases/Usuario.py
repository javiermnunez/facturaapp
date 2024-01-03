from clases.Centro import Centro
from clases.Roll import Roll
from clases.Archivo import Archivo
from clases.Estado import Estado

class Usuario:
    def __init__(self):
        pass
    def __init__(self,id, nombre, apellido, sector, centro, mail, contraseña,roll):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.sector = sector
        self.centro = centro
        self.mail = mail
        self.contraseña = contraseña
        self.roll = roll
        self.aprobados = []
        self.noAprobados = []
        self.usuarios = []


    def buscarArchivo(self,archivoString):
        encontrado = None
        for archivo in self.noAprobados:
            if archivo.cae == archivoString:
                encontrado = archivo
                break
        return encontrado

    def aprobarArchivo(self,archivo):
        if self.roll == Roll.JEFE or self.roll == Roll.GERENTE:
            archivo.cambiarEstado(Estado.APROBADO)
            self.aprobados.append(archivo)
    def eliminarArchivo(self,archivo):
        if self.roll == Roll.JEFE or self.roll == Roll.GERENTE or self.roll == Roll.EMPLEADO:
            if archivo.estado == Estado.NO_APROBADO:
                self.noAprobados.remove(archivo)
    def marcarArchivo(self,archivo):
        if self.roll == Roll.JEFE or self.roll == Roll.GERENTE:
            archivo.cambiarEstado(Estado.MARCADO)



    def __str__(self):
        return f"Usuario: {self.nombre} {self.apellido}\nSector: {self.sector}\nCentro: {self.centro}\nCorreo electrónico: {self.mail}"