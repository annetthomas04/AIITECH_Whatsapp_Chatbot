from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

scope = ['https://spreadsheets.google.com/feeds',
'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\Users\\Annet Thomas\\Downloads\\bot2-464906-4e53a0a0f668.json", scope)
client = gspread.authorize(creds)
sheet = client.open("bot2 details")

# In-memory session store
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

    # Step 1: Category selection
    if session['step'] == 'start':
        session['step'] = 'category'
        return jsonify({'response': "Hi! What are you looking for?\n1. Job\n2. Internship\n3. Course for Kids\n4. Course for Working Professionals"})

    elif session['step'] == 'category':
        if 'job' in message:
            session['data']['type'] = 'Job'
            session['sheet'] = 'Job & Internship'
            session['step'] = 'name'
            return jsonify({'response': "Great! What's your full name?"})
        elif 'internship' in message:
            session['data']['type'] = 'Internship'
            session['sheet'] = 'Job & Internship'
            session['step'] = 'name'
            return jsonify({'response': "Great! What's your full name?"})
        elif 'kids' in message or 'child' in message:
            session['sheet'] = 'Kids Courses'
            session['step'] = 'child_name'
            return jsonify({'response': "What's your child's name?"})
        elif 'professional' in message:
            session['sheet'] = 'Professional Courses'
            session['step'] = 'name'
            return jsonify({'response': "Great! What's your full name?"})
        else:
            return jsonify({'response': "Please choose one of the options: Job, Internship, Course for Kids, or Course for Working Professionals."})

    # Example: Job/Internship flow
    elif session['sheet'] == 'Job & Internship':
        return handle_job_internship_flow(session, message, user_id)
    elif session['sheet'] == 'Kids Courses':
        return handle_kids_courses_flow(session, message, user_id)

    elif session['sheet'] == 'Professional Courses':
        return handle_professional_courses_flow(session, message, user_id)

    return jsonify({'response': "Sorry, I didn't understand that."})

def handle_job_internship_flow(session, message, user_id):
    data = session['data']
    step = session['step']

    if step == 'name':
        data['name'] = message.title()
        session['step'] = 'contact'
        return jsonify({'response': "What's your contact number?"})
    elif step == 'contact':
        data['contact'] = message
        session['step'] = 'location'
        return jsonify({'response': "Where are you located?"})
    elif step == 'location':
        data['location'] = message.title()
        session['step'] = 'visa'
        return jsonify({'response': "What's your visa status?"})
    elif step == 'visa':
        data['visa'] = message
        session['step'] = 'license'
        return jsonify({'response': "Do you have a driving license? (yes/no)"})
    elif step == 'license':
        data['license'] = message
        if data['type'] == 'Internship':
            session['step'] = 'university'
            return jsonify({'response': "Which university are you from?"})
        else:
            session['step'] = 'source'
            return jsonify({'response': "Where did you hear about AIITECH?"})
    elif step == 'university':
        data['university'] = message
        session['step'] = 'course'
        return jsonify({'response': "Which course are you studying?"})
    elif step == 'course':
        data['course'] = message
        session['step'] = 'year'
        return jsonify({'response': "What year are you in, or have you graduated?"})
    elif step == 'year':
        data['year'] = message
        session['step'] = 'source'
        return jsonify({'response': "Where did you hear about AIITECH?"})
    elif step == 'source':
        data['source'] = message
        session['step'] = 'cv'
        return jsonify({'response': "Please upload your CV as a PDF"})
    elif step == 'cv':
        return jsonify({'response': "Waiting for CV upload..."})

    return jsonify({'response': "Something went wrong. Please try again."})

def handle_kids_courses_flow(session, message, user_id):
    data = session['data']
    step = session['step']

    if step == 'child_name':
        data['child_name'] = message.title()
        session['step'] = 'course'
        return jsonify({'response': "Which course is your child interested in?"})
    elif step == 'course':
        data['course'] = message
        session['step'] = 'parent_name'
        return jsonify({'response': "What's the parent's name?"})
    elif step == 'parent_name':
        data['parent_name'] = message.title()
        session['step'] = 'parent_contact'
        return jsonify({'response': "What's the parent's contact number?"})
    elif step == 'parent_contact':
        data['parent_contact'] = message
        session['step'] = 'location'
        return jsonify({'response': "Where are you located?"})
    elif step == 'location':
        data['location'] = message.title()
        session['step'] = 'grade'
        return jsonify({'response': "Which grade is your child studying in?"})
    elif step == 'grade':
        data['grade'] = message
        session['step'] = 'school'
        return jsonify({'response': "Which school does your child go to?"})
    elif step == 'school':
        data['school'] = message
        session['step'] = 'source'
        return jsonify({'response': "Where did you hear about AIITECH?"})
    elif step == 'source':
        data['source'] = message
        save_to_kids_sheet(data)
        user_sessions.pop(user_id)
        return jsonify({'response': "Thanks! Your child's information has been recorded. We'll be in touch soon!"})

    return jsonify({'response': "Something went wrong. Please try again."})

def handle_professional_courses_flow(session, message, user_id):
    data = session['data']
    step = session['step']

    if step == 'name':
        data['name'] = message.title()
        session['step'] = 'contact'
        return jsonify({'response': "What's your contact number?"})
    elif step == 'contact':
        data['contact'] = message
        session['step'] = 'location'
        return jsonify({'response': "Where are you located?"})
    elif step == 'location':
        data['location'] = message.title()
        session['step'] = 'course'
        return jsonify({'response': "Which course are you interested in?"})
    elif step == 'course':
        data['course'] = message
        session['step'] = 'source'
        return jsonify({'response': "Where did you hear about AIITECH?"})
    elif step == 'source':
        data['source'] = message
        save_to_professional_sheet(data)
        user_sessions.pop(user_id)
        return jsonify({'response': "Thanks! Your information has been recorded. We'll be in touch soon!"})

    return jsonify({'response': "Something went wrong. Please try again."})

@app.route('/upload', methods=['POST'])
def upload():
    user_id = request.remote_addr
    session = user_sessions.get(user_id)

    if not session or 'data' not in session:
        return "Session not found", 400

    file = request.files['file']
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Save file path in session data
        session['data']['cv'] = filepath

        # Save to appropriate sheet
        if session['sheet'] == 'Job & Internship':
            save_to_sheet(session['sheet'], session['data'])
        elif session['sheet'] == 'Kids Courses':
            save_to_kids_sheet(session['data'])
        elif session['sheet'] == 'Professional Courses':
            save_to_professional_sheet(session['data'])

        user_sessions.pop(user_id)
        return "CV uploaded and data saved successfully! ✅\n Thanks! Your information has been recorded. We'll be in touch soon!"
    else:
        return "Please upload a valid PDF file.", 400


def save_to_sheet(sheet_name, data):
    worksheet = sheet.worksheet(sheet_name)
    row = [
        data.get('name', ''),
        data.get('contact', ''),
        data.get('location', ''),
        data.get('visa', ''),
        data.get('license', ''),
        data.get('university', ''),
        data.get('course', ''),
        data.get('year', ''),
        data.get('cv', ''),
        data.get('source', ''),
        data.get('type', '')
    ]
    worksheet.append_row(row)

def save_to_kids_sheet(data):
    worksheet = sheet.worksheet("Kids Courses")
    row = [
        data.get('child_name', ''),
        data.get('course', ''),
        data.get('parent_name', ''),
        data.get('parent_contact', ''),
        data.get('location', ''),
        data.get('grade', ''),
        data.get('school', ''),
        data.get('source', '')
    ]
    worksheet.append_row(row)

def save_to_professional_sheet(data):
    worksheet = sheet.worksheet("Professional Courses")
    row = [
        data.get('name', ''),
        data.get('contact', ''),
        data.get('location', ''),
        data.get('course', ''),
        data.get('source', '')
    ]
    worksheet.append_row(row)

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip().lower()
    user_id = request.values.get('From', '')  # e.g. whatsapp:+971xxxxxxx
    resp = MessagingResponse()
    msg = resp.message()

    # Setup user session
    if user_id not in user_sessions:
        user_sessions[user_id] = {'step': 'start', 'data': {}}

    session = user_sessions[user_id]

    # Use existing chatbot logic here
    if session['step'] == 'start':
        session['step'] = 'category'
        msg.body("Hi! What are you looking for?\n1. Job\n2. Internship\n3. Course for Kids\n4. Course for Working Professionals")
    elif session['step'] == 'category':
        if 'job' in incoming_msg:
            session['data']['type'] = 'Job'
            session['sheet'] = 'Job & Internship'
            session['step'] = 'name'
            msg.body("Great! What's your full name?")
        elif 'internship' in incoming_msg:
            session['data']['type'] = 'Internship'
            session['sheet'] = 'Job & Internship'
            session['step'] = 'name'
            msg.body("Great! What's your full name?")
        elif 'kids' in incoming_msg or 'child' in incoming_msg:
            session['sheet'] = 'Kids Courses'
            session['step'] = 'child_name'
            msg.body("What's your child's name?")
        elif 'professional' in incoming_msg:
            session['sheet'] = 'Professional Courses'
            session['step'] = 'name'
            msg.body("Great! What's your full name?")
        else:
            msg.body("Please choose one of the options: Job, Internship, Course for Kids, or Course for Working Professionals")
    elif session['sheet'] == 'Job & Internship':
        return handle_whatsapp_job_flow(session, incoming_msg, msg, user_id)
    elif session['sheet'] == 'Kids Courses':
        return handle_whatsapp_kids_flow(session, incoming_msg, msg, user_id)
    elif session['sheet'] == 'Professional Courses':
        return handle_whatsapp_pro_flow(session, incoming_msg, msg, user_id)

    return str(resp)

def handle_whatsapp_job_flow(session, message, msg, user_id):
    data = session['data']
    step = session['step']

    if step == 'name':
        data['name'] = message.title()
        session['step'] = 'contact'
        msg.body("What's your contact number?")
    elif step == 'contact':
        data['contact'] = message
        session['step'] = 'location'
        msg.body("Where are you located?")
    elif step == 'location':
        data['location'] = message.title()
        session['step'] = 'visa'
        msg.body("What's your visa status?")
    elif step == 'visa':
        data['visa'] = message
        session['step'] = 'license'
        msg.body("Do you have a driving license? (yes/no)")
    elif step == 'license':
        data['license'] = message
        if data['type'] == 'Internship':
            session['step'] = 'university'
            msg.body("Which university are you from?")
        else:
            session['step'] = 'source'
            msg.body("Where did you hear about AIITECH?")
    elif step == 'university':
        data['university'] = message
        session['step'] = 'course'
        msg.body("Which course are you studying?")
    elif step == 'course':
        data['course'] = message
        session['step'] = 'year'
        msg.body("What year are you in, or have you graduated?")
    elif step == 'year':
        data['year'] = message
        session['step'] = 'source'
        msg.body("Where did you hear about AIITECH?")
    elif step == 'source':
        data['source'] = message
        session['step'] = 'cv'
        msg.body("Please upload your CV as a PDF file. You can attach the file here.")
    elif step == 'cv':
        media_count = int(request.values.get('NumMedia', '0'))
        if media_count > 0 and request.values.get('MediaContentType0') == 'application/pdf':
            media_url = request.values.get('MediaUrl0')
            file_data = requests.get(media_url).content
            filename = f"{user_id.replace(':', '_')}_cv.pdf"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as f:
                f.write(file_data)
            session['data']['cv'] = filepath

            # Save to appropriate sheet
            if session['sheet'] == 'Job & Internship':
                save_to_sheet(session['sheet'], session['data'])
            elif session['sheet'] == 'Kids Courses':
                save_to_kids_sheet(session['data'])
            elif session['sheet'] == 'Professional Courses':
                save_to_professional_sheet(session['data'])

            user_sessions.pop(user_id)
            msg.body("✅ CV uploaded successfully!\nThanks! Your information has been recorded. We'll be in touch soon.")
        else:
            msg.body("Please upload your CV as a PDF file. No other formats are accepted.")


    return str(MessagingResponse().append(msg))

def handle_whatsapp_kids_flow(session, message, msg, user_id):
    data = session['data']
    step = session['step']

    if step == 'child_name':
        data['child_name'] = message.title()
        session['step'] = 'course'
        msg.body("Which course is your child interested in?")
    elif step == 'course':
        data['course'] = message
        session['step'] = 'parent_name'
        msg.body("What's the parent's name?")
    elif step == 'parent_name':
        data['parent_name'] = message.title()
        session['step'] = 'parent_contact'
        msg.body("What's the parent's contact number?")
    elif step == 'parent_contact':
        data['parent_contact'] = message
        session['step'] = 'location'
        msg.body("Where are you located?")
    elif step == 'location':
        data['location'] = message.title()
        session['step'] = 'grade'
        msg.body("Which grade is your child studying in?")
    elif step == 'grade':
        data['grade'] = message
        session['step'] = 'school'
        msg.body("Which school does your child go to?")
    elif step == 'school':
        data['school'] = message
        session['step'] = 'source'
        msg.body("Where did you hear about AIITECH?")
    elif step == 'source':
        data['source'] = message
        save_to_kids_sheet(data)
        user_sessions.pop(user_id)
        msg.body("Thanks! Your child's information has been recorded. We'll be in touch soon!")

    return str(MessagingResponse().append(msg))

def handle_whatsapp_pro_flow(session, message, msg, user_id):
    data = session['data']
    step = session['step']

    if step == 'name':
        data['name'] = message.title()
        session['step'] = 'contact'
        msg.body("What's your contact number?")
    elif step == 'contact':
        data['contact'] = message
        session['step'] = 'location'
        msg.body("Where are you located?")
    elif step == 'location':
        data['location'] = message.title()
        session['step'] = 'course'
        msg.body("Which course are you interested in?")
    elif step == 'course':
        data['course'] = message
        session['step'] = 'source'
        msg.body("Where did you hear about AIITECH?")
    elif step == 'source':
        data['source'] = message
        save_to_professional_sheet(data)
        user_sessions.pop(user_id)
        msg.body("Thanks! Your information has been recorded. We'll be in touch soon!")

    return str(MessagingResponse().append(msg))

if __name__ == '__main__':
    app.run(debug=True)
