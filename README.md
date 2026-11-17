# PROJETO-REDES

Servidor HTTP/1.1 feito do zero com sockets TCP em Python, escutando na porta **8880** e seguindo as RFC 9110 e 9112. Não usa nenhum framework: toda a leitura da requisição e a montagem da resposta HTTP são feitas manualmente sobre o socket.

Trabalho da disciplina de Redes de Computadores.

## Funcionalidades

- Atende requisições `GET` vindas do navegador.
- Página de boas-vindas que mostra o IP e a porta de origem do cliente.
- Limite de **5 requisições** seguidas ao `/index.html`. A partir da 6ª, responde **503**.
- Rota `/reiniciar` que zera o limite.
- **404** para qualquer outro recurso, como o `/favicon.ico` que o navegador pede automaticamente.
- **400** para requisições malformadas.
- Toda resposta fecha a conexão (`Connection: close`, conforme a RFC 9112, seção 9.6).
- Logs na tela de cada etapa: abertura e fechamento de sockets, IP e porta do cliente, requisição recebida e resposta enviada.
- Encerramento pelo teclado com `q`.

## Requisitos

- Python 3 (testado no 3.14).
- Nenhuma dependência externa: usa só `socket` e `threading`, da biblioteca padrão.

## Como executar

```bash
python servidor.py
```

Para encerrar, digite `q` e pressione **Enter** no terminal do servidor.

## Rotas

| URL | Resposta |
|---|---|
| `http://IP_DO_SERVIDOR:8880/index.html` | `200 OK` com "Olá, Cliente IP:PORTA !!!". A partir da 6ª requisição, `503 Service Unavailable` |
| `http://IP_DO_SERVIDOR:8880/reiniciar` | `200 OK` e zera o contador do `/index.html` |
| qualquer outro caminho | `404 Not Found` |

Na própria máquina, use `localhost` no lugar de `IP_DO_SERVIDOR`. Para acessar de outro dispositivo da rede, use o IP da máquina (aparece no `ipconfig` ou no `ip a`) e libere o Python no firewall, se for preciso.

## Como funciona

1. O servidor cria um socket TCP/IPv4, faz o `bind` em `0.0.0.0:8880` (todas as interfaces) e entra em `listen`.
2. Uma **thread** separada lê o teclado. Ela é necessária porque o `accept()` bloqueia o fluxo principal. Quando alguém digita `q`, a thread liga uma flag compartilhada.
3. O socket de escuta usa um **timeout de 1 s**. Assim o `accept()` "acorda" periodicamente e o loop consegue conferir essa flag.
4. Para cada conexão, o servidor lê a requisição, separa o método, o caminho e a versão da primeira linha, e escolhe a resposta pela rota.
5. A resposta é montada com a linha de status e os cabeçalhos `Content-Type`, `Content-Length` (em bytes, RFC 9110, seção 8.6) e `Connection: close`, seguidos do corpo HTML. Depois de enviada, o socket do cliente é fechado.

## Exemplo de log

```
Servidor iniciado...
Aguardando conexões na porta 8880...
Aperte a tecla 'q' e aperte ENTER para encerrar o servidor.
Conexão estabelecida com 127.0.0.1:55913
Requisição recebida: 127.0.0.1:55913 GET /index.html HTTP/1.1
200 - (1/5) index.html enviado para 127.0.0.1:55913
Resposta enviada para 127.0.0.1:55913
Conexão com 127.0.0.1:55913 encerrada.
Conexão estabelecida com 127.0.0.1:53075
Requisição recebida: 127.0.0.1:53075 GET /favicon.ico HTTP/1.1
404 - Página não encontrada /favicon.ico requisitada por 127.0.0.1:53075
Resposta enviada para 127.0.0.1:53075
Conexão com 127.0.0.1:53075 encerrada.
Encerrando servidor...
Socket do servidor fechado.
```
