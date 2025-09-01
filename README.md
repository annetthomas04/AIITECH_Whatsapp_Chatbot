# AIITECH WhatsApp Chatbot

An intelligent WhatsApp chatbot developed during my internship at AIITECH to streamline customer engagement and automate support queries. Built using Python, Flask, and Twilio API, this chatbot enhances responsiveness and helps to store generated leads for the educational institution.

## Features

- **Real-time Messaging**: Seamless integration with WhatsApp for instant communication.
- **Intent Recognition**: NLP-powered query handling for accurate and relevant responses.
- **Automated FAQs**: Handles common customer queries with predefined logic.
- **Analytics Logging**: Tracks user interactions for performance insights.
- **Scalable Deployment**: Easily deployable on cloud platforms with secure architecture.

## Technologies Used

- Python  
- Flask  
- Twilio API (WhatsApp Messaging)  
- Ngrok (for local testing)  
- JSON for data handling  

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/annetthomas04/AIITECH_Whatsapp_Chatbot.git
   cd AIITECH_Whatsapp_Chatbot
2. Configure your Twilio credentials and connect the Google Drive API to store customer details into your desired Google Sheet (access my sheet to format the columns and rows as well as the sheets accordingly https://docs.google.com/spreadsheets/d/1AC67dOKmb9JIZze5Mskze503y_zQJ8EDnIgSA0FLr1Y/edit?usp=sharing)
3. When running the program, have it run on the ngrok server and then cop the generated link into Twilio's sandbox testing and add /whatsapp at the end of the link
4. Deploy and test the chatbot by scanning the generated QR code and chatting on Whatsapp.
5. For accessing the uploaded CVs provided by users, follow the path saved to the Google Sheet or locate the chabtot folder directly and retrieve the saved resumes from the uploads folder



