import os
from dotenv import load_dotenv
from Monday_module import Monday

load_dotenv()


def general_ping():
    client = Monday(
        token=os.getenv("MONDAY_API_TOKEN"),
        board_id=int(os.getenv("MONDAY_BOARD_ID")),
    )

    # fetch all board data
    print("Fetching board data...")
    board_data = client.get_board_data()

    # collect IDs of main tasks that are "Working on it"
    working_task_ids = []
    for group_name, group_data in board_data.items():
        for task in group_data["tasks"]:
            if task["columns"].get("project_status") == "Working on it":
                working_task_ids.append(task["id"])
                print(f"  [Working on it] {group_name} → {task['name']!r} (id: {task['id']})")

    print(f"\n{len(working_task_ids)} task(s) currently 'Working on it'.\n")

    # for each task, find its target subtask and inspect it
    for task_id in working_task_ids:
        print(f"--- Task {task_id} ---")

        # fetch full task data including subitems
        task_data = client.get_task_data(task_id)
        print(f"  name: {task_data['name']!r}")

        # find the next subtask to work on (returns a Subtask object)
        subtask = Monday.get_target_subtask(task_data)

        if subtask is None:
            print("  No target subtask found.\n")
            continue

        # call all Subtask methods and print the values
        print(f"  target subtask: {subtask}")
        print(f"    .status:       {subtask.status!r}")
        print(f"    .assignee:     {subtask.assignee!r}")
        print(f"    .last_updated: {subtask.last_updated!r}")
        print()


if __name__ == "__main__":
    general_ping()
