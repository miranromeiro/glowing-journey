from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Counter, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST
from prometheus_flask_exporter import PrometheusMetrics
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:senha@postgres:5432/meubanco'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()

metrics = PrometheusMetrics(app)

USER_REGISTRATION_COUNTER = Counter(
    'user_registration_total', 
    'Total de Requisições de Cadastro de Usuário',
    ['method', 'endpoint', 'status']
)

USER_REGISTRATION_LATENCY = Histogram(
    'user_registration_latency_seconds', 
    'Tempo de Resposta do Cadastro de Usuário',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

USER_REGISTRATION_DURATION = Summary(
    'user_registration_duration_seconds',
    'Tempo total de processamento do cadastro de usuário',
    ['method', 'endpoint']
)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

def init_app():
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

@app.route('/usuario', methods=['POST'])
def criar_usuario():
    start_time = time.time()
    
    try:
        dados = request.get_json()
        
        USER_REGISTRATION_COUNTER.labels(
            method='POST', 
            endpoint='/usuario', 
            status='success'
        ).inc()
        
        novo_usuario = Usuario(nome=dados['nome'])
        db.session.add(novo_usuario)
        db.session.commit()
        
        latency = time.time() - start_time
        
        USER_REGISTRATION_LATENCY.labels(
            method='POST', 
            endpoint='/usuario'
        ).observe(latency)
        
        USER_REGISTRATION_DURATION.labels(
            method='POST', 
            endpoint='/usuario'
        ).observe(latency)
        
        return jsonify({"id": novo_usuario.id, "nome": novo_usuario.nome}), 201
    
    except Exception as e:
        USER_REGISTRATION_COUNTER.labels(
            method='POST', 
            endpoint='/usuario', 
            status='failure'
        ).inc()
        
        return jsonify({"erro": str(e)}), 400

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000)