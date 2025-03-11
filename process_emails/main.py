from google.cloud import aiplatform
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import pickle
import os
import html2text
import functions_framework

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
USER_EMAIL = 'shavkat.aynurin@gmail.com'  # Replace with the target email
LABEL_NAME = 'daily'  # Replace with your label name

def get_gmail_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are not available or are invalid, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def get_emails_with_label(service):
    # Get label ID
    results = service.users().labels().list(userId=USER_EMAIL).execute()
    label_id = None
    for label in results.get('labels', []):
        if label['name'] == LABEL_NAME:
            label_id = label['id']
            break
    
    if not label_id:
        return []
    
    # Get messages with the specified label
    results = service.users().messages().list(
        userId=USER_EMAIL,
        labelIds=[label_id],
        q=f'newer_than:1d'
    ).execute()
    return results.get('messages', [])

def get_email_content(service, msg_id):
    message = service.users().messages().get(
        userId=USER_EMAIL, id=msg_id, format='full').execute()
    
    # Get email body
    if 'payload' in message and 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                text = base64.urlsafe_b64decode(data).decode('utf-8')
                return text
    elif 'payload' in message and 'body' in message['payload']:
        data = message['payload']['body'].get('data', '')
        text = base64.urlsafe_b64decode(data).decode('utf-8')
        return text
    
    return ''

def convert_to_markdown(text):
    h = html2text.HTML2Text()
    h.ignore_links = False
    return h.handle(text)

def summarize_with_gemini(text):
    aiplatform.init(project='your-project-id')  # Replace with your GCP project ID
    
    model = aiplatform.TextGenerationModel.from_pretrained("gemini-2.0-flash-001")
    prompt = f"""Please provide a concise summary of the following email content:

{text}

Summary:"""
    
    response = model.predict(prompt, max_output_tokens=1024)
    return response.text

def send_summary_email(service, summary, original_msg_id):
    message = MIMEText(summary)
    message['to'] = USER_EMAIL
    message['subject'] = 'Email Summary'
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    try:
        service.users().messages().send(
            userId=USER_EMAIL,
            body={'raw': raw, 'threadId': original_msg_id}
        ).execute()
    except Exception as e:
        print(f"Error sending email: {e}")

@functions_framework.http
def process_emails(request):
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Get emails with the specified label
        messages = get_emails_with_label(service)
        
        for message in messages:
            # Get email content
            content = get_email_content(service, message['id'])
            
            # Convert to markdown
            markdown_content = convert_to_markdown(content)
            
            # Get summary from Gemini
            summary = summarize_with_gemini(markdown_content)
            
            # Send summary back to user
            send_summary_email(service, summary, message['id'])
            
            # Remove the label after processing
            service.users().messages().modify(
                userId=USER_EMAIL,
                id=message['id'],
                body={'removeLabelIds': [LABEL_NAME]}
            ).execute()
        
        return 'Emails processed successfully', 200
    except Exception as e:
        return f'Error processing emails: {str(e)}', 500 