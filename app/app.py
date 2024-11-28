from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_flask_exporter import PrometheusMetrics
import time

# Criar a aplicação Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:senha@postgres:5432/meubanco'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o SQLAlchemy sem passar o app inicialmente
db = SQLAlchemy()

# Configurar as métricas do Prometheus
metrics = PrometheusMetrics(app)
REQUEST_COUNT = Counter('app_requests_total', 'Total de Requisições')
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Tempo de Resposta')

# Definir o modelo de usuário
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

# Inicializar o banco de dados com o app
def init_app():
    # Inicializar o db com o app
    db.init_app(app)
    
    # Criar o contexto da aplicação
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()

# Rotas
@app.route('/usuario', methods=['POST'])
@REQUEST_LATENCY.time()
def criar_usuario():
    REQUEST_COUNT.inc()
    dados = request.get_json()
    novo_usuario = Usuario(nome=dados['nome'])
    db.session.add(novo_usuario)
    db.session.commit()
    return jsonify({"id": novo_usuario.id, "nome": novo_usuario.nome}), 201

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Inicialização principal
if __name__ == '__main__':
    # Chamar a função de inicialização
    init_app()
    
    # Iniciar o aplicativo
    app.run(host='0.0.0.0', port=5000)