"""
WhatsApp module for the TTV Automations project.
This module uses Twilio's WhatsApp API (Sandbox in development, WABA in production) to send notifications to assignees.
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


class WhatsApp:
    """Client for sending WhatsApp messages via Twilio."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """
        Args:
            account_sid: Twilio Account SID 
            auth_token: Twilio Auth Token (long secret string)
            from_number: Sender number, digits only, with country code
                         e.g., "14155238886" for the Twilio Sandbox
        """
        self.client = Client(account_sid, auth_token)
        self.from_number = f"whatsapp:+{from_number}"

    def send_message(self, to_number: str, body: str) -> str:
        """
        Send a WhatsApp text message.

        Args:
            to_number: Recipient phone number, digits only, with country code
                       e.g., "61412345678" for an Australian mobile
            body: The message text (free-form for sandbox / inside 24h window;
                  must use approved template in production)

        Returns:
            The Twilio message SID — a unique ID like "SM1234..." used to track
            the message in the Twilio Console.
        """
        message = self.client.messages.create(
            from_=self.from_number,
            to=f"whatsapp:+{to_number}",
            body=body,
        )
        return message.sid


### ---------- TEST ---------- ###
if __name__ == "__main__":
    whatsapp_acc = WhatsApp(
        account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        from_number=os.getenv("TWILIO_WHATSAPP_FROM"),
    )

    MY_NUMBER = "601123266173"

    # --- test send_message ---
    sid = whatsapp_acc.send_message(
        to_number=MY_NUMBER,
        body="🎉 Hello from my TTV Automations bot!",
    )
    print(f"✅ Message sent successfully")
    print(f"   Twilio SID: {sid}")