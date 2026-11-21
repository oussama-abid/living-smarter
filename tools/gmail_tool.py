import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
import google.generativeai as genai

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
]

# Initialize Gemini model once here
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-exp")

def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    service = build("gmail", "v1", credentials=creds)
    return service

def send_email(to_email, subject, body_idea, from_email=None):
    try:
        # Use Gemini to generate a full email body from the subject and idea
        gemini_prompt = f"""
You are an assistant helping write professional and friendly emails.

Write an email based on the following:
- Subject: "{subject}"
- Main message idea: "{body_idea}"

The email should include:
- A polite greeting (e.g., "Hi", "Hello")
- A clear paragraph or two elaborating the message
- A professional closing (e.g., "Best regards", "Thanks")

Respond with only the final email body.
"""
        response = model.generate_content(gemini_prompt)
        formatted_body = response.candidates[0].content.parts[0].text.strip()

        # Compose and send the email using Gmail API
        service = get_gmail_service()
        message = MIMEText(formatted_body)
        message["to"] = to_email
        message["subject"] = subject
        if from_email:
            message["from"] = from_email

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_result = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        return f"Email sent successfully! ID: {send_result['id']}"

    except Exception as error:
        return f"An error occurred while sending email: {error}"


def get_today_email_count():
    try:
        service = get_gmail_service()
        # Gmail date format: YYYY/MM/DD
        today = datetime.date.today()
        # Gmail query format for after: YYYY/MM/DD
        query = f"after:{today.strftime('%Y/%m/%d')}"
        result = service.users().messages().list(userId='me', q=query).execute()
        messages = result.get('messages', [])
        count = len(messages)
        return f"You have {count} email(s) today."
    except Exception as e:
        return f"Error retrieving today's emails: {e}"

def summarize_last_n_emails(n):
    try:
        service = get_gmail_service()
        # Get last n messages (no query to get all)
        result = service.users().messages().list(userId='me', maxResults=n, labelIds=['INBOX']).execute()
        messages = result.get('messages', [])
        if not messages:
            return "No emails found to summarize."

        email_texts = []
        for msg in messages:
            msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['From', 'Subject']).execute()
            headers = msg_detail.get('payload', {}).get('headers', [])
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown sender")
            subject_header = next((h['value'] for h in headers if h['name'] == 'Subject'), "No subject")

            snippet = msg_detail.get('snippet', '')

            # Append sender, subject, snippet for summarization
            email_texts.append(f"From: {from_header}\nSubject: {subject_header}\nSnippet: {snippet}")

        # Prepare prompt for Gemini summarization
        prompt = (
            f"Summarize the following {len(email_texts)} emails briefly, mentioning the sender and main topics:\n\n"
            + "\n\n".join(email_texts)
        )

        response = model.generate_content(prompt)
        summary = response.candidates[0].content.parts[0].text.strip()
        return summary
    except Exception as e:
        return f"Error summarizing emails: {e}"
