from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'votre-clé-secrète')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Affichage des variables d'environnement pour le débogage
print("Client ID:", os.getenv('GOOGLE_CLIENT_ID'))
print("Client Secret:", os.getenv('GOOGLE_CLIENT_SECRET'))

# Configuration OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configuration OAuth avec plus de détails
oauth = OAuth(app)
google_config = {
    'name': 'google',
    'client_id': os.getenv('GOOGLE_CLIENT_ID'),
    'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
    'api_base_url': 'https://www.googleapis.com/oauth2/v2/',
    'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
    'client_kwargs': {
        'scope': 'openid email profile',
        'redirect_uri': 'http://127.0.0.1:5000/login/google/authorize'
    }
}
oauth.register(**google_config)
print("OAuth Config:", google_config)

oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    api_base_url='https://api.github.com/',
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('chatbot'))
        else:
            flash('Email ou mot de passe incorrect')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chatbot'))
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé')
            return redirect(url_for('register'))
        
        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('chatbot'))
    
    return render_template('register.html')

@app.route('/login/google')
def google_login():
    return oauth.google.authorize_redirect(redirect_uri=url_for('google_authorize', _external=True))

@app.route('/login/google/authorize')
def google_authorize():
    token = oauth.google.authorize_access_token()
    resp = oauth.google.get('https://www.googleapis.com/oauth2/v2/userinfo', token=token)
    user_info = resp.json()
    
    user = User.query.filter_by(email=user_info.get('email')).first()
    if not user:
        user = User(
            email=user_info.get('email'),
            name=user_info.get('name', 'Unknown')
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('chatbot'))

@app.route('/login/github')
def github_login():
    return oauth.github.authorize_redirect(redirect_uri=url_for('github_authorize', _external=True))

@app.route('/login/github/authorize')
def github_authorize():
    token = oauth.github.authorize_access_token()
    resp = oauth.github.get('user', token=token)
    user_info = resp.json()
    
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(
            email=user_info['email'],
            name=user_info['login']
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('chatbot'))

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_message = data.get('message', '')
    print("Message reçu:", user_message)  # Debug

    try:
        print("Tentative d'appel à OpenAI...")  # Debug
        # Appel à l'API OpenAI avec la nouvelle syntaxe
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé dans la création de cahiers des charges. Votre rôle est de poser des questions un par un aux utilisateurs pour structurer et rédiger leurs cahiers des charges de manière professionnelle et l'envoyer sous forme word."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500
        )
        print("Réponse OpenAI reçue")  # Debug



        bot_response = response.choices[0].message.content
        print("Réponse:", bot_response)  # Debug
        return jsonify({"response": bot_response})
    except Exception as e:
        print("Erreur:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/test-login')
def test_login():
    return """
    <html>
        <head>
            <title>Test Login</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h2 class="text-center mb-4">Test Connexion</h2>
                                <form method="POST" action="/login">
                                    <div class="mb-3">
                                        <label for="email" class="form-label">Email</label>
                                        <input type="email" class="form-control" id="email" name="email" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="password" class="form-label">Mot de passe</label>
                                        <input type="password" class="form-control" id="password" name="password" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100">Se connecter</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 