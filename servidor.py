"""
Luiz Bonfá dos Santos - RA: a2669609 | Redes de Computadores | Trabalho Servidor TCP/HTTP (2026/2)

DESCRIÇÃO:
    Servidor HTTP/1.1 (RFC 9110 e RFC 9112) feito diretamente com sockets TCP,
    escutando na porta 8880. Responde ao index.html com uma página de boas-vindas
    que mostra o IP e a porta do cliente, limita o acesso a 5 requisições seguidas
    e retorna erro para qualquer outro recurso. Cada resposta encerra a conexão
    (Connection: close). Todas as ações são registradas em log na tela.

REQUISITOS:
    Python 3 (testado no 3.14). Usa apenas bibliotecas padrão (socket e threading), não é necessário instalar nada.

COMO EXECUTAR:
    python servidor.py

COMO TESTAR (no navegador):
    http://IP_DO_SERVIDOR:8880/index.html  -> 200 OK com "Olá, Cliente IP:PORTA !!!"
                                              (a partir da 6ª requisição: 503 Service Unavailable)
    http://IP_DO_SERVIDOR:8880/reiniciar   -> 200 OK e zera o contador do index.html
    Qualquer outro caminho (ex.: /favicon.ico) -> 404 Not Found
    Na própria máquina, use localhost no lugar de IP_DO_SERVIDOR.

COMO ENCERRAR:
    Digite q e pressione ENTER no terminal onde o servidor está rodando.
"""

import socket
import threading

HOST = "0.0.0.0" #Utiliza 0.0.0.0 para que possa receber conexões de outras máquinas
encerrar = False #Flag compartilhada entre thread do teclado e loop.

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET = IPv4 | SOCK_STREAM = TCP
    print("Servidor iniciado...")
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Permite que o socket seja reutilizado imediatamente após o fechamento
    server_socket.bind((HOST, 8880))# O socket é vinculado ao endereço e porta especificados
    server_socket.listen(1) # O servidor começa a escutar por conexões
    print("Aguardando conexões na porta 8880...")
    t = threading.Thread(target=vigiar_teclado, daemon=True)    #Cria uma nova thread para executar a função vigiar_teclado, pois accept() bloqueia, não permitindo a leitura do teclado no mesmo fluxo
                                                                #O daemon = True define que a thread será encerrada assim que o programa inicial for encerrado
    t.start() #Inicia a thread
    print("Aperte a tecla 'q' e aperte ENTER para encerrar o servidor.")
    contador = 0 #Contador fora do while para manter salvo o número de requisições

    server_socket.settimeout(1.0) # O accept desiste após 1 segundo sem conexão, para que seja possível o loop conferir a flag encerrar
    
    while not encerrar: # O loop só se encerra quando a tecla 'q' é digitada no terminal e ENTER é apertado
        try:
            client_socket, address = server_socket.accept() #O servidor aceita a conexão do cliente e retorna um novo socket para comunicação com o cliente e o endereço do cliente
        except socket.timeout: # Quando ninguem se conecta, ele continua o loop sem fazer nada
            continue
        
        print(f"Conexão estabelecida com {address[0]}:{address[1]}")
        
        data = client_socket.recv(1024) #O servidor recebe dados do cliente, com um tamanho máximo de 1024 bytes
        if not data: # Isso ocorre na pré-conexão do navegador, que conecta sem enviar nada.
            print(f"Conexão com {address[0]}:{address[1]} encerrada pelo cliente.")
            client_socket.close()
            continue
        texto = data.decode() #Decodifica os dados recebidos 
        
        primeira_linha = texto.split("\r\n")[0] #Obtém a primeira linha da requisição HTTP
        if len(primeira_linha.split()) != 3: #Verifica se a primeira linha da requisição HTTP está no formato correto
            print(f"Requisição inválida recebida de {address[0]}:{address[1]}")
            resposta = montar_resposta(400, "Bad Request", "<html><body><h1>Requisição inválida.</h1></body></html>") # Armazena a resposta de requisição inválida
            client_socket.sendall(resposta) # Envia a resposta ao cliente
            client_socket.close()
            continue
        
        metodo, caminho, versao = primeira_linha.split() #Obtém o método, caminho e versão da requisição HTTP
        print(f"Requisição recebida: {address[0]}:{address[1]} {metodo} {caminho} {versao}")
        if caminho == "/index.html": #Verifica se o caminho da requisição é /index.html
            if contador >= 5: #Verifica se o contador de requisições excedeu o limite de 5 requisições de /index.html antes do += 1 para que ele conte as requisições da forma correta, pois contador começa em 0
                print(f"503 - Limite de requisições excedido {address[0]}:{address[1]}")
                resposta = montar_resposta(503, "Service Unavailable", "<html><body><h1>Limite de requisições excedido.</h1></body></html>") # Armazena a resposta de limite de requisições excedido
            else:
                contador += 1 #Conta a quantidade de requisições de /index.html
                print(f"200 - ({contador}/5) index.html enviado para {address[0]}:{address[1]}")
                resposta = montar_resposta(200, "OK", f"<html><body><h1>Olá, Cliente {address[0]}:{address[1]} !!!</h1></body></html>")
        #Reiniciar contador
        elif caminho == "/reiniciar": #Verifica se o caminho da requisição é /reiniciar
            contador = 0 # Reinicia o contador de requisições
            print(f"Contador de requisições reiniciado por {address[0]}:{address[1]}")
            resposta = montar_resposta(200, "OK", "<html><body><h1>Contador de requisições reiniciado.</h1></body></html>") # Armazena a resposta de contador reiniciado
        else: #Else é utilizado para que qualquer requisição fora do escopo determinado não seja encontrada.
            print(f"404 - Página não encontrada {caminho} requisitada por {address[0]}:{address[1]}")
            resposta = montar_resposta(404, "Not Found", "<html><body><h1>Página não encontrada.</h1></body></html>") #Armazena a resposta de página não encontrada

        #O envio ocorre ao fim das verificações para uma melhor estrutura de código, caso não fosse assim, todo local que possui um resposta =... teria um envio, funciona, porém piora compreensão
        client_socket.sendall(resposta) # Envia a resposta ao cliente
        print(f"Resposta enviada para {address[0]}:{address[1]}")
        client_socket.close()
        print(f"Conexão com {address[0]}:{address[1]} encerrada.")
        
    print("Encerrando servidor...")
    server_socket.close()
    print("Socket do servidor fechado.")
    
# Função para montar a resposta HTTP
def montar_resposta(codigo, frase, corpo):
    corpo = corpo.encode()  # Converte o corpo da resposta para bytes, caso contasse caracteres a informação de tamanho (Que é convencionada em bytes) se torna incorreta.
                            #Ex: len("à") = 1 / quantidade de bytes de à = 2
    resposta = f"HTTP/1.1 {codigo} {frase}\r\n" # Monta a primeira linha da resposta HTTP com o código de status e a frase correspondente
    resposta += "Content-Type: text/html; charset=utf-8\r\n" # Adiciona o cabeçalho Content-Type indicando que o corpo da resposta é HTML
    resposta += f"Content-Length: {len(corpo)}\r\n" # Adiciona o cabeçalho Content-Length indicando o tamanho do corpo da resposta em bytes, utilizando o padrão da RFC 9110, seção 8.6.
    resposta += "Connection: close\r\n" # Adiciona o cabeçalho Connection indicando que a conexão será fechada após a resposta, utilizando o padrão da RFC 9112, seção 9.6
    resposta += "\r\n" # Adiciona uma linha em branco para separar os cabeçalhos do corpo da resposta
    return resposta.encode() + corpo # Converte a resposta completa para bytes antes de enviá-la ao cliente

#Função utilizada para receber a tecla q do teclado, quem ativa ela é a thread criada no inicio da main
def vigiar_teclado():
    global encerrar # O Global é utilizado para que não seja criada uma nova variável de nome encerrar no escopo de vigiar_teclado e utilize a variável global definida no inicio do código
    while True:
        if input().strip().lower() == 'q':
            encerrar = True
            break
            
if __name__ == "__main__":
    main()