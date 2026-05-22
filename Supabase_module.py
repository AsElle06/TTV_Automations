"""
Supabase module.
This module is the linkage layer between Monday and WhatsApp.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class Supabase:

    """Client for accessing the assignee lookup table in Supabase."""

    TABLE_NAME = "assignee_data"

    def __init__(self, url: str, key: str):
        """
        Args:
            url: Supabase project URL (from Settings → API)
            key: Supabase anon or service role key
        """
        self.client: Client = create_client(url, key)

    def get_whatsapp_num(self, monday_acc: str) -> str | None:
        """
        Look up the WhatsApp number for a given Monday assignee.

        Args:
            monday_acc: The Monday person column value (e.g., "Suling Lim" or "suling19094@gmail.com")

        Returns:
            The WhatsApp number as a string, or None if no record exists
            for this assignee.
        """
        result = (
            self.client.table(self.TABLE_NAME)
            .select("whatsapp_num")
            .eq("monday_acc", monday_acc)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return result.data[0]["whatsapp_num"]


### ---------- TEST ---------- ###
if __name__ == "__main__":
    client = Supabase(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_KEY"),
    )

    # --- test get_whatsapp_num ---
    # Test with a real name from your table
    number = client.get_whatsapp_num("Suling Lim")
    print(f"Number: {number}")
    # Test with a name that doesn't exist
    missing = client.get_whatsapp_num("Nonexistent Person")
    print(f"Missing: {missing}")