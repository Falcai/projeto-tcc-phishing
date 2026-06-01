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
    <title>Cartilha de Segurança Digital</title>
    <style>
        :root {
            --primary: #2c3e50;
            --danger: #e74c3c;
            --bg: #f4f7f6;
            --card-bg: #ffffff;
            --text: #333333;
        }
        body {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background-color: var(--bg);
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .aviso-topo {
            background-color: #f8d7da;
            color: #721c24;
            padding: 15px 20px;
            border-radius: 8px;
            border-left: 6px solid #dc3545;
            margin-bottom: 30px;
            font-size: 0.95em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .hero {
            text-align: center;
            padding: 40px 20px;
            background-color: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 30px;
            border-top: 5px solid var(--danger);
        }
        .hero h1 {
            color: var(--danger);
            margin-top: 0;
            font-size: 2.2em;
        }
        .hero p.lead {
            font-size: 1.1em;
            color: #555;
        }
        .cartilha-section {
            background: var(--card-bg);
            padding: 35px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }
        .cartilha-section h2 {
            color: var(--primary);
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .perfil {
            background-color: #e8f4f8;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #3498db;
        }
        .dicas-grid {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .dica-card {
            background: #fdfdfd;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 20px;
            display: flex;
            align-items: flex-start;
            gap: 15px;
            transition: transform 0.2s ease;
        }
        .dica-card:hover {
            transform: translateX(5px);
            border-color: #bdc3c7;
        }
        .dica-icon {
            font-size: 2em;
            line-height: 1;
            min-width: 40px;
            text-align: center;
        }
        .dica-texto h3 {
            margin: 0 0 8px 0;
            color: var(--primary);
            font-size: 1.1em;
        }
        .dica-texto p {
            margin: 0;
            font-size: 0.95em;
            color: #555;
        }
        .highlight {
            background-color: #ffeaa7;
            padding: 0 4px;
            border-radius: 3px;
            font-weight: 500;
        }
        .github-section {
            text-align: center;
            margin-top: 20px;
            padding: 25px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        .github-btn {
            display: inline-block;
            background-color: #24292e;
            color: #ffffff;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin-top: 15px;
            transition: background 0.3s;
        }
        .github-btn:hover {
            background-color: #000000;
            color: #ffffff;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #dee2e6;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Aviso Legal -->
        <div class="aviso-topo">
            <strong>⚠️ AVISO DE PESQUISA:</strong> Este site é parte de um Trabalho de Conclusão de Curso (TCC). <strong>Nenhum dado pessoal seu foi roubado ou exposto.</strong>
        </div>

        <!-- Cabeçalho de Impacto -->
        <header class="hero">
            <h1>Você clicou em um link suspeito!</h1>
            <p class="lead">Mas fique calmo(a), você está seguro. Se este fosse um ataque real de <strong>Phishing</strong>, suas senhas ou dados bancários poderiam estar em risco agora.</p>
        </header>

        <!-- Introdução -->
        <section class="cartilha-section">
            <div class="perfil">
                <strong>Olá! Meu nome é Felipe Falcai.</strong><br>
                Sou estudante de Engenharia de Computação na Universidade de Araraquara (Uniara). Criei este site como um experimento prático para o meu TCC focado em Segurança da Informação, para mostrar como é fácil cairmos em truques na internet.
            </div>
            
            <h2>O que é Phishing?</h2>
            <p>O cibercrime percebeu que é muito mais fácil "hackear" a mente de uma pessoa do que quebrar a segurança de um servidor. O <strong>phishing</strong> (que vem de <em>fishing</em>, pescar em inglês) é um golpe onde o criminoso usa e-mails ou mensagens falsas se passando por empresas de confiança (bancos, lojas, RH) para "pescar" seus dados.</p>
            <p>Eles costumam usar gatilhos emocionais para te fazer clicar sem pensar, como o <strong>medo</strong> ("sua conta será bloqueada") ou a <strong>ganância</strong> ("você ganhou um prêmio").</p>
        </section>

        <!-- Cartilha de Dicas -->
        <section class="cartilha-section">
            <h2>Cartilha de Defesa: Como não ser fisgado</h2>
            <p style="margin-bottom: 25px;">A melhor proteção contra golpes na internet é a desconfiança. Adote estas 4 regras de ouro no seu dia a dia:</p>
            
            <div class="dicas-grid">
                <div class="dica-card">
                    <div class="dica-icon">🔍</div>
                    <div class="dica-texto">
                        <h3>Verifique o Remetente com lupa</h3>
                        <p>O nome de exibição pode ser "Banco X", mas ao clicar para ver o e-mail real, você encontra algo esquisito como <span class="highlight">suporte@banco-atualizacao.com</span>. Empresas verdadeiras usam seus endereços oficiais.</p>
                    </div>
                </div>

                <div class="dica-card">
                    <div class="dica-icon">🔒</div>
                    <div class="dica-texto">
                        <h3>A ilusão do Cadeado (HTTPS)</h3>
                        <p>Antigamente, diziam que sites com o cadeadinho verde eram seguros. <strong>Hoje, isso é um mito.</strong> O cadeado apenas indica que a conexão é embaralhada, mas o site pode muito bem ser de um criminoso. Sempre leia o nome do site (URL) lá em cima.</p>
                    </div>
                </div>

                <div class="dica-card">
                    <div class="dica-icon">🛑</div>
                    <div class="dica-texto">
                        <h3>A Regra do "Não Clique"</h3>
                        <p>Recebeu um SMS ou e-mail alarmante pedindo urgência? <strong>Não clique no link da mensagem.</strong> Feche tudo, abra o aplicativo ou digite o site oficial do seu banco no navegador para conferir se o aviso é real.</p>
                    </div>
                </div>

                <div class="dica-card">
                    <div class="dica-icon">🔤</div>
                    <div class="dica-texto">
                        <h3>Atenção a erros de digitação sutis</h3>
                        <p>Criminosos imitam endereços famosos trocando apenas uma letra ou número, como <span class="highlight">www.amaz0n.com</span> ou <span class="highlight">www.faceb00k.com</span>. Olhe com calma antes de colocar sua senha.</p>
                    </div>
                </div>
            </div>
            
            <!-- Link para o GitHub -->
            <div class="github-section">
                <strong>👨‍💻 Interessado na parte técnica?</strong><br>
                Este projeto tem código aberto! Se você é estudante, desenvolvedor ou apenas curioso para saber como o servidor e o banco de dados funcionam por trás dos panos, sinta-se à vontade para visitar a arquitetura.
                <br>
                <a href="https://github.com/Falcai/projeto-tcc-phishing" target="_blank" class="github-btn">
                    Acessar Repositório no GitHub
                </a>
            </div>
        </section>

        <!-- Rodapé de Estatísticas -->
        <footer class="footer">
            Estatística do Experimento: Até o momento, <strong>{{ total_cliques }}</strong> dispositivos únicos acessaram esta página.<br>
            <small>Para garantir sua privacidade (LGPD), os endereços IP não são armazenados em texto claro, mas sim convertidos em códigos anônimos irretratáveis.</small>
        </footer>
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