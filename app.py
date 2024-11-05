from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import os
import threading
import time
import webbrowser
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuração do CORS - permitir apenas o frontend em localhost:8000
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})  # Permitir apenas localhost:8000

# Configuração do JWT
app.config['JWT_SECRET_KEY'] = 'sua_chave_secreta'  # Troque isso por uma chave secreta mais segura
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # O token expira em 1 hora
jwt = JWTManager(app)

DATA_FILE = 'financas.txt'

# Endpoint para login
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    # Valide as credenciais (isso é apenas um exemplo)
    if username == 'usuario' and password == 'senha':
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Credenciais inválidas"}), 401

@app.route('/adicionar', methods=['POST'])
@jwt_required()
def adicionar():
    data = request.json
    descricao = data.get('descricao')
    valor = data.get('valor')
    categoria = data.get('categoria')

    if descricao and valor is not None:
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(DATA_FILE, 'a') as f:
            f.write(f'{descricao},{valor},{categoria},{data_atual}\n')
        return jsonify({"message": "Registro adicionado com sucesso!"}), 200
    return jsonify({"message": "Dados inválidos!"}), 400

@app.route('/historico', methods=['GET'])
@jwt_required()
def historico():
    if not os.path.exists(DATA_FILE):
        return jsonify([])

    with open(DATA_FILE, 'r') as f:
        linhas = f.readlines()
    
    transacoes = []
    for linha in linhas:
        descricao, valor, categoria, data = linha.strip().split(',')
        transacoes.append({
            'descricao': descricao,
            'valor': float(valor),
            'categoria': categoria,
            'data': data
        })
    
    return jsonify(transacoes)

@app.route('/buscar', methods=['GET'])
@jwt_required()
def buscar():
    termo = request.args.get('termo', '').lower()
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')

    if not os.path.exists(DATA_FILE):
        return jsonify([])

    with open(DATA_FILE, 'r') as f:
        linhas = f.readlines()

    transacoes = []
    for linha in linhas:
        # Verifique se a linha tem pelo menos 4 partes (descricao, valor, categoria, data)
        try:
            descricao, valor, categoria, data = linha.strip().split(',')
        except ValueError:
            continue  # Ignorar linhas mal formatadas

        # Filtro por descrição, categoria ou data
        if termo in descricao.lower() or termo in categoria.lower() or termo in data:
            # Filtro adicional por intervalo de datas
            if data_inicio and data_fim:
                try:
                    data_obj = datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
                    inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                    fim = datetime.strptime(data_fim, '%Y-%m-%d')
                    if inicio <= data_obj <= fim:
                        transacoes.append({
                            'descricao': descricao,
                            'valor': float(valor),
                            'categoria': categoria,
                            'data': data
                        })
                except ValueError:
                    continue  # Ignorar se a data não estiver no formato esperado
            else:
                transacoes.append({
                    'descricao': descricao,
                    'valor': float(valor),
                    'categoria': categoria,
                    'data': data
                })

    return jsonify(transacoes)

@app.route('/relatorio', methods=['GET'])
@jwt_required()
def relatorio():
    if not os.path.exists(DATA_FILE):
        return jsonify({"entradas_totais": 0, "saidas_totais": 0, "saldo_final": 0})

    with open(DATA_FILE, 'r') as f:
        linhas = f.readlines()

    entradas_totais = 0
    saidas_totais = 0

    for linha in linhas:
        descricao, valor, categoria, data = linha.strip().split(',')
        valor = float(valor)
        if categoria == 'Entrada':
            entradas_totais += valor
        else:
            saidas_totais += valor

    saldo_final = entradas_totais - saidas_totais

    return jsonify({
        "entradas_totais": entradas_totais,
        "saidas_totais": saidas_totais,
        "saldo_final": saldo_final
    })

@app.route('/fechar', methods=['POST'])
@jwt_required()
def fechar():
    return jsonify({"message": "Serviço encerrado!"}), 200

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8000'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# Aqui está o ponto de alteração: adicionar o método GET para /saldo
@app.route('/saldo', methods=['GET'])
@jwt_required()
def saldo():
    if not os.path.exists(DATA_FILE):
        return jsonify({"saldo": 0})

    with open(DATA_FILE, 'r') as f:
        linhas = f.readlines()

    entradas_totais = 0
    saidas_totais = 0

    for linha in linhas:
        descricao, valor, categoria, data = linha.strip().split(',')
        valor = float(valor)
        if categoria == 'Entrada':
            entradas_totais += valor
        else:
            saidas_totais += valor

    saldo_final = entradas_totais - saidas_totais

    return jsonify({"saldo": saldo_final})


# A rota OPTIONS deve ser mais generalizada para permitir o CORS
@app.route('/saldo', methods=['OPTIONS'])
def options_saldo():
    return '', 200

def start_flask():
    app.run(port=5000)

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        open(DATA_FILE, 'w').close()

    # Inicia o servidor Flask em uma thread separada
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # Aguarda um pouco para garantir que o Flask esteja em funcionamento
    time.sleep(3)

    # Abre o navegador apenas uma vez
    webbrowser.open("http://localhost:8000/")

    # Inicia o servidor HTTP
    os.system("python -m http.server 8000")
