import sqlite3

conexao = sqlite3.connect("banco_local.db")
cursor = conexao.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS disp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nSerie TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    status TEXT NOT NULL,
                    local TEXT NOT NULL,
                    chamado TEXT
                )
            """)

# Definindo a classe Pos
class Pos:
    idCont = 1  # Contador para ID

    def __init__(self, nSerie, modelo):
        self.id = Pos.idCont  # Atribui o valor de idCont ao atributo id da instância
        Pos.idCont += 1  # Incrementa o contador global
        self.nSerie = nSerie
        self.modelo = modelo
        self.status = "Disponível"
        self.local = "Payer"
        self.chamado = None
        self.obs = None
    
    def mostrar_atributos(self):
        for atributo, valor in self.__dict__.items():
            print(f"{atributo}: {valor}")

    def solicitar_troca(self):
        ##cursor.execute("""""")
        if(self.status == "Disponível"):
            self.status = "Troca em aberto"
            print("Solicitação de troca aberta")
        else:
            print("Dispositivo não válido para troca")
    
    def receberPos(self):
        if(self.status == "Troca em aberto"):
            self.status = "Aguardando voucher" 
            print("Insira as informações do dispositivo recebido")
            nSerie = input("Número de série: ")
            modelo = input("Modelo: ")
            return Pos(nSerie, modelo)
        else:
            print("Dispositivo não tem troca em aberto")
    
    def devolver(self):
        if(self.status == "Aguardando voucher"):
            self.status = "Troca concluída"
            print("Dispositivo devolvido com sucesso!")
        else: 
            print("Dispositivo inválido para devolução")
    
    @classmethod
    def dispExiste(cls, nSerie, dispositivos):
        for disp in dispositivos:
            if disp.nSerie == nSerie:
                return disp
        return None

    @classmethod
    def dispExisteDB(cls, nSerie):
        cursor.execute("SELECT id FROM disp WHERE nSerie = ?", (nSerie,))
        resultado = cursor.fetchone()
        if(resultado):
            return resultado[0]
        else:
            return None

class PosData:
    idCont = 1  # Contador para ID

    def __init__(self, id, nSerie, modelo, status, local, chamado, obs):
        self.id = id
        self.nSerie = nSerie
        self.modelo = modelo
        self.status = status
        self.local = local
        self.chamado = chamado
        self.obs = obs

    def update(id, status):
        cursor.execute("""UPDATE disp SET status = ?  WHERE id = ?""", (status, id))

    ##def create():

# Inserindo as instâncias de dispositivos na tabela 'disp' do banco de dados
##for pos in dispositivos:
##    cursor.execute("""
##        INSERT INTO disp (nSerie, modelo, status, local) 
##        VALUES (?, ?, ?, ?)
##    """, (pos.nSerie, pos.modelo, pos.status, pos.local))

# Confirmando a transação
conexao.commit()

# Buscando dados da tabela
cursor.execute("SELECT * FROM disp")
tabela = cursor.fetchall()

dispositivos = []

for linha in tabela:
    dispositivos.append(PosData(linha[0], linha[1], linha[2], linha[3], linha[4], linha[5], linha[6]))

for linha in dispositivos:
     print(f"ID: {linha[0]}, nSerie: {linha[1]}, Modelo: {linha[2]}, Status: {linha[3]}, Local: {linha[4]}, Chamado: {linha[5]}, Obs: {linha[6]}")

# Operações no menu
opcao = 1
while opcao != 0:
    for i, pos in enumerate(dispositivos):
        print(f"Índice: {i}, ID: {pos.nSerie}, Nome: {pos.modelo}, Status: {pos.status}")
    opcao = int(input("\nO que deseja fazer?\n0. Sair\n1. Solicitar troca\n2. Receber dispositivo\n3. Devolver\n> "))
    
    match opcao:
        case 0:
            print("Cancelando!")
        case 1:
            nSerie = input("Informe o Número de série do dispositivo:\n> ")
            if (dispEncontrado := Pos.dispExisteDB(nSerie)):
                dispositivos[dispEncontrado-1].solicitar_troca()
            else:
                print("Dispositivo não encontrado")
        case 2: 
            nSerie = input("Informe o Número de série do dispositivo com troca em andamento:\n> ")
            if (dispEncontrado := Pos.dispExiste(nSerie, dispositivos)):
                dispEncontrado.receberPos()
            else:
                print("Dispositivo não encontrado")
        case 3:
            nSerie = input("Informe o número de série do equipamento:\n> ")
            if (dispEncontrado := Pos.dispExiste(nSerie, dispositivos)):
                dispEncontrado.devolver()
            else:
                print("Dispositivo não encontrado")
        case _:
            print("Opção inválida")
    print("-------------------------------------------------------")

# Fechar o cursor e a conexão
cursor.close()
conexao.close()
