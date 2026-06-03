"""
WhatsApp module for the TTV Automations project.
This module uses Twilio's WhatsApp API (Sandbox in development, WABA in production) to send notifications to assignees.
"""

import os
import json
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
        normalized = from_number.removeprefix("whatsapp:").lstrip("+")
        self.from_number = f"whatsapp:+{normalized}"

    def send_message(self, to_number: str, content_sid: str, content_variables: dict | None = None) -> str:
        """
        Send a WhatsApp message using a Twilio content template.

        Args:
            to_number: Recipient phone number, digits only, with country code
                       e.g., "61412345678" for an Australian mobile
            content_sid: The template SID from Twilio Content Editor, e.g. "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            content_variables: Optional dict mapping placeholder indices to values,
                               e.g. {"1": "Suling Lim", "2": "Edit video"}

        Returns:
            The Twilio message SID — a unique ID like "SM1234..." used to track
            the message in the Twilio Console.
        """
        to_normalized = to_number.removeprefix("whatsapp:").lstrip("+")
        message = self.client.messages.create(
            from_=self.from_number,
            to=f"whatsapp:+{to_normalized}",
            content_sid=content_sid,
            content_variables=json.dumps(content_variables) if content_variables else None,
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
        content_sid=os.getenv("TWILIO_CONTENT_SID_NEWTASK"),
        content_variables={"1": "Suling Lim", "2": "Edit video"},
    )
    print(f"Message sent successfully")
    print(f"   Twilio SID: {sid}")