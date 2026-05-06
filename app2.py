from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
import requests
import os

app = Flask(__name__)
app.secret_key = "cle_secrete_oathnet"

# Chemin vers la base de données
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    essais = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verifier', methods=['POST'])
def verifier():
    email_saisi = request.form.get('email').lower().strip()
    
    # 1. On récupère ou on crée l'utilisateur
    user = User.query.filter_by(email=email_saisi).first()
    if not user:
        user = User(email=email_saisi, essais=0)
        db.session.add(user)
        db.session.commit()

    # 2. BLOQUAGE : Si déjà 2 essais ou plus, STOP.
    if user.essais >= 2:
        return render_template('abonnement.html')

    # 3. APPEL API (vrais résultats)
    API_KEY = "4caf18f810864153bc7347c52f800f28"
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email_saisi}"
    headers = {"hibp-api-key": API_KEY, "user-agent": "python-app"}
    
    try:
        response = requests.get(url, headers=headers)
        resultats = response.json() if response.status_code == 200 else []
    except:
        resultats = []

    # 4. ON COMPTE L'ESSAI MAINTENANT
    user.essais += 1
    db.session.commit()
    
    # 5. ON ENVOIE TOUT (avec le compteur)
    return render_template('resultats.html', 
                           email=email_saisi, 
                           breaches=resultats, 
                           nb_recherches=user.essais)

if __name__ == '__main__':
    app.run(debug=True)
    