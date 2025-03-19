from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mediaid.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class UserHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    dob = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(10))
    emergency_name = db.Column(db.String(50))
    emergency_phone = db.Column(db.String(15))
    emergency_relation = db.Column(db.String(50))
    medical_conditions = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    blood_type = db.Column(db.String(5))
    location_services = db.Column(db.Boolean)
    notifications = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Make sure this runs within the app context
with app.app_context():
    db.create_all()

# Mistral API credentials
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_AGENT_ID = os.getenv("MISTRAL_AGENT_ID")

def call_mistral_agent(prompt):
    """
    Calls the Mistral API to get a response for the given prompt.
    """
    url = "https://api.mistral.ai/v1/agents/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "agent_id": MISTRAL_AGENT_ID,  # Pass agent ID correctly
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise HTTPError for 4xx or 5xx errors
        response_json = response.json()
        
        # Debugging: Print full API response
        print("Mistral API Response:", response_json)

        # Extract the bot's response
        return response_json.get("choices", [{}])[0].get("message", {}).get("content", "Error: No response from agent.")
    except requests.exceptions.RequestException as e:
        return f"Error: Failed to connect to Mistral agent: {e}"
    except ValueError as e:
        return f"Error: Invalid JSON response from Mistral agent: {e}"
    except KeyError:
        return "Error: Could not extract response from JSON"

# Default route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/first')
def first():
    return render_template('first.html')

@app.route('/maps')
def maps():
    return render_template('maps.html')

@app.route('/history-page')
def history_page():
    all_data = UserHistory.query.all()
    return render_template('history.html', history_data=all_data)

# Form submission route
@app.route('/submit', methods=['POST'])
def submit():
    data = request.form  # Changed to receive form data from HTML form

    # Create a new history record
    new_entry = UserHistory(
        first_name=data.get('firstName'),
        last_name=data.get('lastName'),
        email=data.get('email'),
        phone=data.get('phone'),
        dob=data.get('dob'),
        gender=data.get('gender'),
        address=data.get('address'),
        city=data.get('city'),
        state=data.get('state'),
        zip_code=data.get('zipCode'),
        emergency_name=data.get('emergencyName'),
        emergency_phone=data.get('emergencyPhone'),
        emergency_relation=data.get('emergencyRelation'),
        medical_conditions=data.get('medicalConditions'),
        medical_history=data.get('medicalHistory'),
        blood_type=data.get('bloodType'),
        location_services=bool(data.get('locationServices', False)),
        notifications=bool(data.get('notifications', False))
    )

    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'message': 'User data saved successfully!'}), 200

@app.route('/history', methods=['GET'])
def history():
    all_data = UserHistory.query.all()
    output = []

    for data in all_data:
        output.append({
            'firstName': data.first_name,
            'lastName': data.last_name,
            'email': data.email,
            'phone': data.phone,
            'dob': data.dob,
            'gender': data.gender,
            'address': data.address,
            'city': data.city,
            'state': data.state,
            'zipCode': data.zip_code,
            'emergencyName': data.emergency_name,
            'emergencyPhone': data.emergency_phone,
            'emergencyRelation': data.emergency_relation,
            'medicalConditions': data.medical_conditions,
            'medicalHistory': data.medical_history,
            'bloodType': data.blood_type,
            'locationServices': data.location_services,
            'notifications': data.notifications,
            'timestamp': data.timestamp
        })
    
    return jsonify(output)

# Chatbot route
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# Chat API endpoint
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('user_input')
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    
    response = call_mistral_agent(user_input)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)