# Gmail Summarizer Cloud Run Function

This Cloud Run function automatically processes emails with a specific label, summarizes them using Google's Gemini AI model, and sends the summaries back to the user.

## Prerequisites

1. Google Cloud Project with the following APIs enabled:
   - Cloud Run
   - Gmail API
   - Vertex AI API

2. Gmail account with OAuth 2.0 credentials
3. Service account with necessary permissions

## Setup Instructions

1. Create OAuth 2.0 credentials:
   - Go to Google Cloud Console > APIs & Services > Credentials
   - Create OAuth 2.0 Client ID
   - Download the credentials and save as `credentials.json` in the project directory

2. Update the configuration in `main.py`:
   - Set `USER_EMAIL` to your Gmail address
   - Set `LABEL_NAME` to the Gmail label you want to monitor
   - Update the `project` parameter in `summarize_with_gemini()` with your GCP project ID

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Deploy to Cloud Run:
   ```bash
   gcloud run deploy gmail-summarizer \
     --source . \
     --region your-region \
     --platform managed \
     --allow-unauthenticated
   ```

## Usage

1. Create a label in Gmail (e.g., "ToSummarize")
2. Apply this label to any email you want to be summarized
3. The Cloud Run function will:
   - Process emails with the specified label
   - Convert email content to markdown
   - Generate a summary using Gemini
   - Send the summary back to you
   - Remove the label from the processed email

## Security Note

Store your credentials securely and never commit them to version control. Use Google Cloud Secret Manager for production deployments. 