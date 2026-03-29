from flask import Flask, request, render_template_string, Response
import hashlib
import os
import psycopg2
from datetime import datetime
import csv
import io

app = Flask(__name__)

# pega a URL de conexão do banco configurada no Render
DATABASE_URL = os.environ.get('DATABASE_URL')
TOKEN_SECRETO = 'senha_tcc_123' # token para baixar o banco de dados em .CSV

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aviso de Segurança - Projeto Acadêmico</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: auto; color: #333; }
        .alerta { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; border-left: 5px solid #f5c6cb; margin-bottom: 20px; }
        .conteudo { background-color: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
        h1 { color: #d9534f; }
        .footer { margin-top: 30px; font-size: 0.9em; color: #666; text-align: center; border-top: 1px solid #ddd; padding-top: 10px; }
    </style>
</head>
<body>
    <div class="alerta">
        <strong>⚠️ AVISO:</strong> Este site é parte de um Trabalho de Conclusão de Curso (TCC). Nenhum dado pessoal foi exposto.
    </div>

    <div class="conteudo">
        <h1>Você clicou em um link suspeito!</h1>
        <p>Se este fosse um ataque real de <strong>Phishing</strong>, suas informações poderiam estar em risco.</p>
        <h2>O que é Phishing?</h2>
        <p>É uma técnica de engenharia social onde o atacante se disfarça de uma entidade confiável para enganar vítimas e induzi-las a clicar em links maliciosos ou fornecer informações sensíveis.</p>
    </div>

    <div class="footer">
        Estatística: Até o momento, <strong>{{ total_cliques }}</strong> dispositivos únicos acessaram esta página. <br>
        <em>Os IPs são anonimizados via hash e armazenados em banco de dados para fins acadêmicos.</em>
    </div>
</body>
</html>
"""

def get_db_connection():
    if not DATABASE_URL:
        print("AVISO: DATABASE_URL não configurada!")
        return None
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    if conn is None:
        return
        
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acessos (
            id SERIAL PRIMARY KEY,
            ip_hash TEXT UNIQUE,
            data_acesso TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# inicializa o banco assim que o app sobe
init_db()

@app.route('/')
def index():
    ip_usuario = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if ip_usuario and ',' in ip_usuario:
        ip_usuario = ip_usuario.split(',')[0].strip()
        
    total_cliques = 0
    
    if ip_usuario:
        ip_hash = hashlib.sha256(ip_usuario.encode('utf-8')).hexdigest()
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO acessos (ip_hash, data_acesso) 
                VALUES (%s, %s)
                ON CONFLICT (ip_hash) DO NOTHING
            ''', (ip_hash, datetime.now()))
            conn.commit()
            
            cursor.execute('SELECT COUNT(*) FROM acessos')
            total_cliques = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
        
    return render_template_string(HTML_TEMPLATE, total_cliques=total_cliques)

@app.route('/exportar-dados')
def exportar_dados():
    token_fornecido = request.args.get('token')
    if token_fornecido != TOKEN_SECRETO:
        return "Acesso negado. Token inválido ou ausente.", 403

    conn = get_db_connection()
    if not conn:
        return "Erro de conexão com o banco de dados.", 500
        
    cursor = conn.cursor()
    cursor.execute('SELECT id, ip_hash, data_acesso FROM acessos ORDER BY data_acesso ASC')
    registros = cursor.fetchall()
    
    cursor.close()
    conn.close()

    saida_csv = io.StringIO()
    escritor = csv.writer(saida_csv)
    escritor.writerow(['ID', 'Hash_do_IP', 'Data_e_Hora_do_Acesso'])
    escritor.writerows(registros)

    resposta = Response(saida_csv.getvalue(), mimetype='text/csv')
    resposta.headers["Content-Disposition"] = "attachment; filename=dados_phishing.csv"
    
    return resposta

@app.route('/ping') #rota criada para manter o servidor do Render sempre acordado
def ping():
    return "Estou acordado!", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)