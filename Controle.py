from peewee import *
import datetime
import json
import requests 
import tkinter as tk 
from tkinter import ttk

with open("request_data.json", "r", encoding="utf-8") as arquivo:
    dadosRequest = json.load(arquivo)

requestBody = {
    "customer_id": dadosRequest["customer_id"],
    "customer_id_type": dadosRequest["customer_id_type"],
    "department_id": dadosRequest["department_id"],
    "category_id": dadosRequest["category_id"],
    "subject": dadosRequest["subject"],
    "priority": dadosRequest["priority"],
    "message": dadosRequest["message"]
}

db = SqliteDatabase("banco_local.db")

# Definindo a classe Pos
class Pos(Model):
    id = AutoField()
    nSerie = CharField()
    modelo = CharField()
    status = CharField(default="Disponível")
    local = CharField(default="Payer")
    protocolo = CharField(null=True)
    idChamado = CharField()
    dtaAberturaTroca = DateTimeField(null=True)
    dtaDevolucao =  DateTimeField(null=True)
    obs = TextField(null=True)
    
    class Meta:
        database = db
        table_name = 'pos'
    
    def mostrar_atributos(self):
        for atributo, valor in self.__dict__.items():
            print(f"{atributo}: {valor}")

    @classmethod
    def dispExiste(cls, nSerie):
        for dispositivo in dispositivos:
            if dispositivo.nSerie == nSerie:
                return dispositivo
        return None

    def solicitar_troca(self):
        if(self.status == "Disponível"):
            defeito = input("Informe a falha apresentada no equipamento: ")
            self.status = "Troca em aberto"
            self.dtaAberturaTroca = datetime.datetime.now()
            reqBodyCopia = requestBody.copy()
            reqBodyCopia["message"] = f"Necessário realizar a troca de um dipositivo POS Payer via Portal Jira\n\nNSG:{self.nSerie}\nModelo: {self.modelo}\nEstabelecimento: {self.local}\n\nMotivo: {defeito}"
            response = requests.post(dadosRequest["urlCriacao"], headers = {"Authorization": dadosRequest["Authorization"]}, data=reqBodyCopia)
            responseJson = response.json()
            if(responseJson["error"] == False):
                self.idChamado = responseJson["ticket_id"]
                self.protocolo = responseJson["protocol"]
                self.save()
                print(f"Chamado #{responseJson["protocol"]} criado com sucesso!")
            else:
                print(f"Falha ao criar chamado, {responseJson["message"]} {responseJson["errorcode"]}")
        else:
            print("Dispositivo não válido para troca")
    
    def receberPos(self):
        if(self.status == "Troca em aberto"):
            self.status = "Aguardando voucher"
            ##self.save()
            print("Insira as informações do dispositivo recebido")
            nSerie = input("Número de série: ")
            modelo = input("Modelo: ")
            if(not self.dispExiste(nSerie)):
                response = requests.post(
                    dadosRequest["urlReplyCustumer"],
                    headers={"Authorization": dadosRequest["Authorization"]},
                    data={"ticket_id": self.idChamado, "message": f"Respectivo dispositivo enviado na troca chegou ao local, NSG: {nSerie}, aguardando envio de Voucher para logística reversa"}
                    )
                responseJson = response.json()
                if(responseJson["error"] == False):print("Resposta enviado com sucesso no chamado!")
                else: print(f"Falha ao enviar resposta, {responseJson["message"]} {responseJson["errorcode"]}")
                self.save()
                Pos.create(
                    nSerie=nSerie,
                    modelo=modelo, 
                    status="Disponível", 
                    local="Payer", 
                    protocolo=None, 
                    idChamado=None,
                    dtaAberturaTroca=None, 
                    dtaDevolucao=None, 
                    obs=None
                )
            else:
                print("Dispositivo já existe na base de dados!")
        else:
            print("Dispositivo não tem troca em aberto")
    
    def devolver(self):
        if(self.status == "Aguardando voucher"):
            self.status = "Troca concluída"
            self.dtaDevolucao = datetime.datetime.now()
            response = requests.post(dadosRequest["urlFinalization"], headers= {"Authorization": dadosRequest["Authorization"]}, data={"ticketId": self.idChamado, "message": "Dispositivo encaminhado via Correios para Gertec"})
            responseJson = response.json()
            if(responseJson["error"] ==  False):
                print("Chamando finalizado com sucesso!")
            else:
                print(f"Falha finalizar chamado, {responseJson["message"]} {responseJson["errorcode"]}")
            self.save()
            print("Dispositivo devolvido com sucesso!")
        else: 
            print("Dispositivo inválido para devolução")

db.connect()
db.create_tables([Pos])

dispositivos = Pos.select()

root = tk.Tk()

root.title("Gerenciador de dispositivos")
root.geometry("1400x500")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

aba1 = ttk.Frame(notebook)
aba2 = ttk.Frame(notebook)
aba3 = ttk.Frame(notebook)
aba4 = ttk.Frame(notebook)

notebook.add(aba1, text="Todos")
notebook.add(aba2, text="Disponíveis")
notebook.add(aba3, text="Em andamento")
notebook.add(aba4, text="Finalizado")

colunasTabela = ("nSerie", "Modelo", "Status", "Local", "Chamado", "Andamento")
lbl1 = tk.Label(aba1, text="Todos dispositivos estarão aqui", font=("arial", 12))
lbl1.pack(pady=20)

tabelaTodosDisp = ttk.Treeview(aba1, columns=colunasTabela, show="headings")
tabelaTodosDisp.heading("nSerie", text="Número de série Gertec")
tabelaTodosDisp.heading("Modelo", text="Modelo")
tabelaTodosDisp.heading("Status", text="Status")
tabelaTodosDisp.heading("Local", text="Local")
tabelaTodosDisp.heading("Chamado", text="Chamado")
tabelaTodosDisp.heading("Andamento", text="Andamento")

tabelaTodosDisp.column("nSerie", width=190, anchor="center")
tabelaTodosDisp.column("Modelo", width=70, anchor="center")
tabelaTodosDisp.column("Status", width=70, anchor="center")
tabelaTodosDisp.column("Local", width=70, anchor="center")
tabelaTodosDisp.column("Chamado", width=70, anchor="center")
tabelaTodosDisp.column("Andamento", width=70, anchor="center")

for dispositivo in dispositivos:
    if dispositivo.status != "Devolvida":
        dataInserida = (dispositivo.nSerie, dispositivo.modelo, dispositivo.status, dispositivo.local, dispositivo.protocolo, None)
        tabelaTodosDisp.insert("", "end", values=dataInserida)

tabelaTodosDisp.pack(fill="y", expand=True)

lbl2 = tk.Label(aba2, text="Dispositivos disponíveis", font=("arial", 12))
lbl2.pack(pady=20)
lbl3 = tk.Label(aba3, text="Dispostivos com troca em andamento", font=("arial", 12))
lbl3.pack(pady=20)
lbl4 = tk.Label(aba4, text="Dispositivos já devolvidos", font=("arial", 12))
lbl4.pack(pady=20)

root.mainloop()
# Operações no menu
# opcao = 1
# while opcao != 0:
#     #Buscando dados da tabela
#     dispositivos = Pos.select()
    
#     for dispositivo in dispositivos:
#         print(f"ID: {dispositivo.id}, nSerie: {dispositivo.nSerie}, Modelo: {dispositivo.modelo}, Status: {dispositivo.status}, Local: {dispositivo.local}, Chamado: {dispositivo.protocolo}, Abertura: {dispositivo.dtaAberturaTroca}")
    
#     opcao = int(input("\nO que deseja fazer?\n0. Sair\n1. Solicitar troca\n2. Receber dispositivo\n3. Devolver\n4. Definir estabelecimento\n> "))
    
#     match opcao:
#         case 0:
#             print("Cancelando!")
#         case 1:
#             nSerie = input("Informe o Número de série do dispositivo:\n> ")
#             if (dispEncontrado := Pos.dispExiste(nSerie)):
#                 dispEncontrado.solicitar_troca()
#             else:
#                 print("Dispositivo não encontrado")
#         case 2: 
#             nSerie = input("Informe o Número de série do dispositivo com troca em andamento:\n> ")
#             if (dispEncontrado := Pos.dispExiste(nSerie)):
#                 dispEncontrado.receberPos()
#             else:
#                 print("Dispositivo não encontrado")
#         case 3:
#             nSerie = input("Informe o número de série do equipamento:\n> ")
#             if (dispEncontrado := Pos.dispExiste(nSerie)):
#                 dispEncontrado.devolver()
#             else:
#                 print("Dispositivo não encontrado")
#         case 4:
#             nSerie = input("Qual o dispositivo que deseja alterar o local?")
#             if(dispEncontrado := Pos.dispExiste(nSerie)):
#                 local = input("Qual local será definido? ")
#                 dispEncontrado.local = local
#                 dispEncontrado.save()
#         case _:
#             print("Opção inválida")
#     db.close()
#     print("-----------------------------------------------------------------------------------")