
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

    def __str__(self):
        return f"Usuario: {self.nombre} {self.apellido}\nSector: {self.sector}\nCentro: {self.centro}\nCorreo electrónico: {self.mail}"