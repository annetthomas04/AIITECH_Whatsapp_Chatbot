from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Flask(__name__)

scope = ['https://spreadsheets.google.com/feeds',
'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\Users\\Annet Thomas\\Downloads\\bot2-464906-2fbbdbcec974.json", scope)
client = gspread.authorize(creds)
sheet = client.open("bot2 details").sheet1

user_sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_id = request.remote_addr
    message = request.json['message'].strip().lower()

    if user_id not in user_sessions:
        user_sessions[user_id] = {'step': 'start', 'data': {}}

    session = user_sessions[user_id]

    if session['step'] == 'start':
        session['step'] = 'category'
        return jsonify({'response': "Hi! What are you looking for?\n1. Job or Internship\n2. Courses for Kids\n3. Courses for Working Professionals"})

    elif session['step'] == 'category':
        if 'job' in message:
            session['data']['category'] = 'Job or Internship'
        elif 'kid' in message:
            session['data']['category'] = 'Courses for Kids'
        elif 'professional' in message:
            session['data']['category'] = 'Courses for Working Professionals'
        else:
            return jsonify({'response': "Please choose one of the options: Job or Internship, Courses for Kids, or Courses for Working Professionals."})

        session['step'] = 'name'
        return jsonify({'response': "Great! What's your full name?"})

    elif session['step'] == 'name':
        session['data']['name'] = message.title()
        session['step'] = 'contact'
        return jsonify({'response': "Thanks! What's your contact number?"})

    elif session['step'] == 'contact':
        session['data']['contact'] = message
        session['step'] = 'location'
        return jsonify({'response': "Got it. Where are you located?"})

    elif session['step'] == 'location':
        session['data']['location'] = message.title()
        save_to_sheet(session['data'])
        user_sessions.pop(user_id)
        return jsonify({'response': "Thanks! Your information has been recorded in our system. We'll be in touch soon!"})

    return jsonify({'response': "Sorry, I didn't understand that."})

def save_to_sheet(data):
    sheet.append_row([data['name'], data['contact'], data['location'], data['category']])

if __name__ == '__main__':
    app.run(debug=True)
