from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client 
import requests
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# configure your own twilio account and copy the generated twilio account credentials that you are provided with
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACXXXXXXXXXXXXXXXX")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "6XXXXXXXXXXXXXXXX")

#configure google sheets API and generate a json file and link its location to store responses in a google sheet connected to your google drive
scope = ['https://spreadsheets.google.com/feeds',
'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("C:\\path\\to\\your\\credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("name_of_your_google_sheet")

user_sessions = {}

class ChatBot:
    def __init__(self):
        self.categories = {
            '1': 'job',
            '2': 'internship',
            '3': 'kids',
            '4': 'professional'
        }

    def classify_message(self, message):
        message_lower = message.lower()

        job_keywords = ['job', 'employment', 'work', 'career', 'position', 'hiring']
        internship_keywords = ['internship', 'intern', 'training', 'experience']
        kids_keywords = ['kids', 'children', 'child', 'school', 'young']
        professional_keywords = ['professional', 'course', 'certification', 'training', 'skill']

        if any(keyword in message_lower for keyword in job_keywords):
            return 'job'
        elif any(keyword in message_lower for keyword in internship_keywords):
            return 'internship'
        elif any(keyword in message_lower for keyword in kids_keywords):
            return 'kids'
        elif any(keyword in message_lower for keyword in professional_keywords):
            return 'professional'
        return None

    def get_welcome_message(self):
        return """Welcome! 👋 
        
I'm here to help you find what you're looking for. Please select an option:

1️⃣ Job Opportunities  
2️⃣ Internship Programs  
3️⃣ Kids Courses  
4️⃣ Professional Courses

Reply with the number (1-4) or describe what you're looking for."""

    def get_category_message(self, category):
        messages = {
            'job': "Great! You're looking for job opportunities. 💼\n\nPlease share your full name to proceed.",
            'internship': "Excellent! You're interested in internship programs. 🎓\n\nPlease share your full name to get started.",
            'kids': "Wonderful! You're looking for kids courses. 🏫\n\nWhat's your child's name?",
            'professional': "Perfect! You're interested in professional courses. 📚\n\nPlease share your full name to begin."
        }
        return messages.get(category, "Please select a valid category.")

bot = ChatBot()

@app.route('/')
def index():
    return render_template('index.html')

def download_pdf_from_whatsapp(media_url, filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        response = requests.get(media_url, stream=True, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return filepath
        else:
            print(f"Failed to download PDF: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None

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
    try:
        incoming_msg = request.values.get('Body', '').strip().lower()
        user_id = request.values.get('From', '')
        resp = MessagingResponse()
        msg = resp.message()

        if user_id not in user_sessions:
            user_sessions[user_id] = {'step': 'start', 'data': {}}

        session = user_sessions[user_id]

        media_count = int(request.values.get('NumMedia', '0'))
        if media_count > 0:
            media_content_type = request.values.get('MediaContentType0', '')
            if 'pdf' in media_content_type.lower():
                return handle_pdf_upload(session, user_id, msg, resp)

        if session['step'] == 'start':
            session['step'] = 'category'
            msg.body(bot.get_welcome_message())

        elif session['step'] == 'category':

            choice_map = {
                '1': 'job',
                '2': 'internship',
                '3': 'kids',
                '4': 'professional'
            }

            user_input = incoming_msg.strip().lower()
            category = choice_map.get(user_input)

            if not category:
                category = bot.classify_message(user_input)

            if category == "job":
                session['data']['type'] = 'Job'
                session['sheet'] = 'Job & Internship'
                session['step'] = 'name'
                msg.body(bot.get_category_message('job'))

            elif category == "internship":
                session['data']['type'] = 'Internship'
                session['sheet'] = 'Job & Internship'
                session['step'] = 'name'
                msg.body(bot.get_category_message('internship'))

            elif category == "kids":
                session['sheet'] = 'Kids Courses'
                session['step'] = 'child_name'
                msg.body(bot.get_category_message('kids'))

            elif category == "professional":
                session['sheet'] = 'Professional Courses'
                session['step'] = 'name'
                msg.body(bot.get_category_message('professional'))

            else:
                msg.body("Please choose a valid option:\n1. Job\n2. Internship\n3. Course for Kids\n4. Course for Working Professionals")

        elif session['sheet'] == 'Job & Internship':
            handle_whatsapp_job_flow(session, incoming_msg, msg, user_id)
        elif session['sheet'] == 'Kids Courses':
            handle_whatsapp_kids_flow(session, incoming_msg, msg, user_id)
        elif session['sheet'] == 'Professional Courses':
            handle_whatsapp_pro_flow(session, incoming_msg, msg, user_id)

        return str(resp)
    
    except Exception as e:
        print(f"Error in WhatsApp webhook: {e}")
        resp = MessagingResponse()
        msg = resp.message()
        msg.body("Sorry, something went wrong. Please try again by typing 'start'.")
        return str(resp)

def handle_pdf_upload(session, user_id, msg, resp):

    try:
        if session['step'] != 'cv':
            msg.body("Please complete the information form first before uploading your CV.")
            return str(resp)
        
        media_url = request.values.get('MediaUrl0')
        now = datetime.now()
        date_str = now.strftime("%b%d")      # e.g. Jul21
        time_str = now.strftime("%H%M")      # e.g. 1057

        full_name = session['data'].get('name', 'Unknown').replace(' ', '')
        phone_number = user_id.replace('whatsapp:', '')

        filename = f"{full_name}_{phone_number}_{date_str}_{time_str}.pdf"

        filepath = download_pdf_from_whatsapp(media_url, filename)
        
        if filepath:
            session['data']['cv'] = filename
            
            if session['sheet'] == 'Job & Internship':
                save_to_sheet(session['sheet'], session['data'])
            elif session['sheet'] == 'Professional Courses':
                save_to_professional_sheet(session['data'])
            
            user_sessions.pop(user_id, None)
            
            msg.body("✅ CV uploaded successfully!\nThanks! Your information has been recorded. We'll be in touch soon.")
        else:
            msg.body("Sorry, there was an issue downloading your CV. Please try uploading again.")
            
    except Exception as e:
        print(f"Error handling PDF upload: {e}")
        msg.body("Sorry, there was an error processing your CV. Please try again.")
    
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
        msg.body("Please upload your CV as a PDF file. You can attach the file to your next message.")
    elif step == 'cv':
        msg.body("Please attach a PDF file with your CV. I'm waiting for your file upload.")

def handle_whatsapp_kids_flow(session, message, msg, user_id):
    data = session['data']
    step = session['step']

    if step == 'child_name':
        data['child_name'] = message.title()
        session['step'] = 'course'
        msg.body("""For kids, here are the courses we provide:

1️⃣ Robotics and AI  
2️⃣ Coding for Kids  
3️⃣ Python Programming  

Which course is your child interested in?""")

    elif step == 'course':
        courses = {
            '1': 'Robotics and AI',
            '2': 'Coding for Kids',
            '3': 'Python Programming'
        }
        selected = message.strip()
        data['course'] = courses.get(selected, selected.title())
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
        user_sessions.pop(user_id, None)
        msg.body("Thanks! Your child's information has been recorded. We'll be in touch soon!")

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
        msg.body("""For working professionals, here are the courses we provide:

1️⃣ Artificial Intelligence  
2️⃣ Machine Learning with AI  
3️⃣ Data Science & Analytics  
4️⃣ Python Programming  
5️⃣ FullStack Development  
6️⃣ Digital Marketing with AI  
7️⃣ Graphic Designing with AI  
8️⃣ Power BI  
9️⃣ Advanced Excel  

Which course are you interested in?""")

    elif step == 'course':
        courses = {
            '1': 'Artificial Intelligence',
            '2': 'Machine Learning with AI',
            '3': 'Data Science & Analytics',
            '4': 'Python Programming',
            '5': 'FullStack Development',
            '6': 'Digital Marketing with AI',
            '7': 'Graphic Designing with AI',
            '8': 'Power BI',
            '9': 'Advanced Excel'
        }
        selected = message.strip()
        data['course'] = courses.get(selected, selected.title())
        session['step'] = 'source'
        msg.body("Where did you hear about AIITECH?")

    elif step == 'source':
        data['source'] = message
        save_to_professional_sheet(data)
        user_sessions.pop(user_id, None)
        msg.body("Thanks! Your information has been recorded. We'll be in touch soon!")

@app.route('/test', methods=['GET'])
def test():
    return "WhatsApp ChatBot is running! 🤖"

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'active',
        'active_sessions': len(user_sessions),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("WhatsApp ChatBot starting...")
    app.run(debug=True)