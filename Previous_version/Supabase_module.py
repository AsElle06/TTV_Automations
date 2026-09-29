"""
Supabase module for the TTV Automations Project.
This module is the linkage layer between Monday, Frame.io and WhatsApp.
"""

import os
from supabase import create_client, Client
from datetime import datetime, timezone
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
    
    def update_previous_ping(self, monday_acc: str) -> bool:
        """
        Set `previous_ping` to the current UTC time for the given assignee.

        Args:
            monday_acc: The Monday assignee name to update

        Returns:
            True if a row was updated, False if no matching record exists.
        """
        now_utc = datetime.now(timezone.utc).isoformat()

        result = (
            self.client.table(self.TABLE_NAME)
            .update({"previous_ping": now_utc})
            .eq("monday_acc", monday_acc)
            .execute()
        )

        return len(result.data) > 0


### ---------- TEST ---------- ###
if __name__ == "__main__":
    supabase_table = Supabase(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_KEY"),
    )

    # --- Test get_whatsapp_num ---
    print("--- Test get_whatsapp_num ---")
    number = supabase_table.get_whatsapp_num("Suling Lim")
    print(f"Number: {number}")

    # --- Test get_whatsapp_num (missing) ---
    missing = supabase_table.get_whatsapp_num("Nonexistent Person")
    print(f"Missing: {missing}")

    # --- Test update_previous_ping ---
    print("\n--- Test update_previous_ping ---")
    success = supabase_table.update_previous_ping("Suling Lim")
    print(f"Updated: {success}")

    # --- Test update_previous_ping (missing) ---
    print("\n--- Test update_previous_ping (missing) ---")
    success = supabase_table.update_previous_ping("Nonexistent Person")
    print(f"Updated: {success}")

    # --- Verify previous_ping was set ---
    print("\n--- Verify previous_ping was set ---")
    result = (
        supabase_table.client.table(supabase_table.TABLE_NAME)
        .select("monday_acc, previous_ping")
        .eq("monday_acc", "Suling Lim")
        .execute()
    )
    print(result.data)