# Event-Driven Messaging Platform

An event-driven messaging platform for sending personalized WhatsApp messages using Twilio and Flask. This application listens for incoming events and triggers corresponding actions, such as sending tailored messages to users.

## Features

- Receive incoming WhatsApp messages.
- Process messages in an event-driven manner.
- Webhook support for real-time message and status updates.

## Tech Stack

- **Backend:** Python, Flask
- **Messaging:** Twilio API for WhatsApp
- **Development:** ngrok

## Prerequisites

Before you begin, ensure you have the following installed:
- [Python 3.8+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [ngrok](https://ngrok.com/download)
- A [Twilio account](https://www.twilio.com/try-twilio) with a configured WhatsApp Sandbox.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd event-driven-messaging-platform
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Set up local tunneling with ngrok:**
    To allow Twilio to send requests to your local Flask application, you need to expose your local server to the internet.
    ```bash
    ngrok http 5000
    ```
    Note down the `https` Forwarding URL provided by ngrok (e.g., `https://<random-string>.ngrok.io`).

2.  **Configure Twilio Sandbox:**
    - Go to your Twilio Console and navigate to the WhatsApp Sandbox settings.
    - In the "WHEN A MESSAGE COMES IN" field, paste your ngrok URL followed by the webhook endpoint (e.g., `https://<random-string>.ngrok.io/webhook`).
    - You can use the same URL for the "STATUS CALLBACK URL" to receive message status updates.

![alt text](image.png)
