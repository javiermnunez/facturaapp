from clases.Estado import Estado
class Archivo:
    def __init__(self, id, cuit, razonSocial, cae, fechaCarga, fechaModificacion,importe):
        self.id = id
        self.cuit = cuit
        self.razonSocial = razonSocial
        self.cae = cae
        self.fechaCarga = fechaCarga
        self.fechaModificacion = fechaModificacion
        self.importe = importe
        self.estado = Estado.NO_APROBADO
    def __init__(self):
        pass
    
    def cambiarEstado(self,Estado):
        self.estado = Estado