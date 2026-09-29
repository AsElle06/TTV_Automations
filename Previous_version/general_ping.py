import os
from datetime import timedelta
from dotenv import load_dotenv
from Monday_module import Monday
from Supabase_module import Supabase
from Whatsapp_module import WhatsApp

load_dotenv()

ONE_DAY = timedelta(minutes=1)

print()
def general_ping():
    monday = Monday(
        token=os.getenv("MONDAY_API_TOKEN"),
        board_id=int(os.getenv("MONDAY_BOARD_ID")),
    )
    supabase = Supabase(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_KEY"),
    )
    wa = WhatsApp(
        account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        from_number=os.getenv("TWILIO_WHATSAPP_FROM"),
    )

    print("Fetching board data...")
    board_data = monday.get_board_data()

    working_task_ids = []
    for group_name, group_data in board_data.items():
        for task in group_data["tasks"]:
            if task["columns"].get("project_status") == "Working on it":
                working_task_ids.append(task["id"])
                print(f"  [Working on it] {group_name} → {task['name']!r} (id: {task['id']})")

    print(f"\n{len(working_task_ids)} task(s) currently 'Working on it'.\n")

    for task_id in working_task_ids:
        print(f"--- Task {task_id} ---")

        task_data = monday.get_task_data(task_id)

        # --- Reminder: subtask is 'Working on it' and stale ---
        stale_subtask = Monday.get_stale_subtask(task_data, ONE_DAY)
        if stale_subtask:
            assignee = stale_subtask.assignee
            whatsapp_num = supabase.get_whatsapp_num(assignee) if assignee else None
            if whatsapp_num:
                sid = wa.send_message(
                    to_number=whatsapp_num,
                    content_sid=os.getenv("TWILIO_CONTENT_SID_REMINDER"),
                    content_variables={
                        "1": assignee,
                        "2": task_data["name"],
                        "3": stale_subtask.name,
                        "4": stale_subtask.id,
                    },
                )
                print(f"  Reminder sent to {assignee!r} for stale subtask {stale_subtask.name!r} → SID: {sid}")
            else:
                print(f"  Stale subtask {stale_subtask.name!r} — no WhatsApp number found for {assignee!r}, skipping.")

        # --- New task: subtask is 'Not Started' and next in sequence ---
        target_subtask = Monday.get_target_subtask(task_data)

        if target_subtask is None:
            print("  No target subtask found.\n")
            continue

        print(f"  Target subtask: {target_subtask}")

        assignee = target_subtask.assignee
        if not assignee:
            print("  No assignee found on subtask, skipping.\n")
            continue

        whatsapp_num = supabase.get_whatsapp_num(assignee)
        if not whatsapp_num:
            print(f"  No WhatsApp number found for {assignee!r}, skipping.\n")
            continue

        sid = wa.send_message(
            to_number=whatsapp_num,
            content_sid=os.getenv("TWILIO_CONTENT_SID_NEWTASK"),
            content_variables={
                "1": assignee,
                "2": task_data["name"],
                "3": target_subtask.name,
                "4": target_subtask.id,
            },
        )
        print(f"  Notified {assignee!r} → SID: {sid}\n")


if __name__ == "__main__":
    general_ping()
