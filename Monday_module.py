import os
import time
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class Monday:

    API_URL = "https://api.monday.com/v2"
    API_VERSION = "2024-10"

    def __init__(self, token: str, board_id: int):
        """
        Args:
            token: Personal Monday API Token
            board_id: the board from Monday that this module will work on
        """
        self.token = token
        self.board_id = board_id
        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "API-Version": self.API_VERSION,
        }

    def _post_query(self, query: str, variables: dict | None = None, _retried: bool = False) -> dict:
        """
        Send a GraphQL request to Monday and return the parsed JSON.
        Automatically retries once on 429 using the retry_in_seconds from the response body.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.API_URL,
            json=payload,
            headers=self.headers,
            timeout=30,
        )

        if response.status_code == 429:
            # Prefer header; fall back to JSON body (Monday often omits the header)
            retry_after = int(response.headers.get("Retry-After", 0))
            if not retry_after:
                try:
                    retry_after = response.json()["errors"][0]["extensions"].get("retry_in_seconds", 60)
                except Exception:
                    retry_after = 60

            if not _retried:
                time.sleep(retry_after)
                return self._post_query(query, variables, _retried=True)

            raise Exception(
                f"Monday rate limit hit (429). "
                f"Retry after: {retry_after} seconds. "
                f"Body: {response.text}"
            )

        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise Exception(f"Monday API error: {data['errors']}")

        return data

    def get_board_summary(self) -> dict:
        """
        A brief summary/overview of the board
        Fetch metadata for the board: id, name, description,
        and a flat list of its groups (id + title).
        """
        query = """
        query ($board_id: [ID!]) {
        boards(ids: $board_id) {
            id
            name
            description
            groups {
            id
            title
            }
        }
        }
        """
        variables = {"board_id": [str(self.board_id)]}
        data = self._post_query(query, variables)
        return data["data"]["boards"][0]

    def get_board_data(self) -> dict[str, dict]:
        """
        Comprehensive data of every group on the board, including each
        group's ID, its tasks, and every task's column values.

        Format:
            {
                "Requests": {
                    "id": "new_group29179",
                    "tasks": [
                        {
                            "id": "2700464157",
                            "name": "task 1",
                            "columns": {
                                "project_owner": "Suling Lim",
                                "project_status": "Not Started",
                                "pulse_updated": "2026-05-14 02:55:40 UTC"
                            }
                        },
                        ...
                    ]
                },
                "Pre-production": {
                    "id": "new_group43041",
                    "tasks": [...]
                }
            }

        Strategy: two-step fetch to minimise complexity budget usage.
          1. Cheap groups query to build the group-id → title map.
          2. Board-level items_page (not nested inside groups) with cursor-based
             pagination via next_items_page at the query root, far lower complexity
             than nesting items_page inside every group.
        """
        # Step 1: fetch groups (lightweight)
        groups_query = """
        query ($board_id: [ID!]) {
        boards(ids: $board_id) {
            groups {
            id
            title
            }
        }
        }
        """
        groups_data = self._post_query(groups_query, {"board_id": [str(self.board_id)]})
        groups = groups_data["data"]["boards"][0]["groups"]

        result: dict[str, dict] = {}
        group_title_by_id: dict[str, str] = {}
        for group in groups:
            result[group["title"]] = {"id": group["id"], "tasks": []}
            group_title_by_id[group["id"]] = group["title"]

        # Step 2: fetch all items via board-level items_page (first page)
        # items carry group.id so we can slot them into the right group.
        first_page_query = """
        query ($board_id: [ID!]) {
        boards(ids: $board_id) {
            items_page(limit: 100) {
            cursor
            items {
                id
                name
                group { id }
                column_values(ids: ["project_owner", "project_status", "pulse_updated"]) {
                id
                text
                }
            }
            }
        }
        }
        """

        # Subsequent pages use next_items_page at root — much cheaper than
        # re-running the full boards query.
        next_page_query = """
        query ($cursor: String!) {
        next_items_page(limit: 100, cursor: $cursor) {
            cursor
            items {
            id
            name
            group { id }
            column_values(ids: ["project_owner", "project_status", "pulse_updated"]) {
                id
                text
            }
            }
        }
        }
        """

        data = self._post_query(first_page_query, {"board_id": [str(self.board_id)]})
        page = data["data"]["boards"][0]["items_page"]

        while True:
            for item in page["items"]:
                group_id = item["group"]["id"]
                group_title = group_title_by_id.get(group_id)
                if group_title:
                    columns = {col["id"]: col["text"] for col in item["column_values"]}
                    result[group_title]["tasks"].append({
                        "id": item["id"],
                        "name": item["name"],
                        "columns": columns,
                    })

            cursor = page.get("cursor")
            if not cursor:
                break

            data = self._post_query(next_page_query, {"cursor": cursor})
            page = data["data"]["next_items_page"]

        return result
    
    def get_task_data(self, task_id: int | str) -> dict:
        """
        Fetch a single task and all of its subitems.
        Args:
            task_id: The item ID of the task
        Returns:
            {
                "id": "2700464157",
                "name": "task name",
                "columns": {
                    "project_owner": "Suling Lim",
                    "project_status": "Not Started",
                    "pulse_updated": "2026-05-14 02:55:40 UTC"
                },
                "subitems": [
                    {
                        "id": "subitem_id",
                        "name": "subitem name",
                        "columns": {
                            "person": "Suling Lim",
                            "status": "Not Started",
                            "pulse_updated_mm3jq690": "2026-05-21 02:08:18 UTC"
                        }
                    },
                    ...
                ]
            }
        """
        query = """
        query ($item_id: [ID!]) {
        items(ids: $item_id) {
            id
            name
            column_values(ids: ["project_owner", "project_status", "pulse_updated"]) {
            id
            text
            }
            subitems {
            id
            name
            column_values(ids: ["person", "status", "pulse_updated_mm3jq690"]) {
                id
                text
            }
            }
        }
        }
        """
        data = self._post_query(query, {"item_id": [str(task_id)]})
        items = data["data"]["items"]

        if not items:
            raise ValueError(f"Task {task_id} not found")

        item = items[0]
        subitems = [
            {
                "id": sub["id"],
                "name": sub["name"],
                "columns": {col["id"]: col["text"] for col in sub["column_values"]},
            }
            for sub in (item.get("subitems") or [])
        ]

        return {
            "id": item["id"],
            "name": item["name"],
            "columns": {col["id"]: col["text"] for col in item["column_values"]},
            "subitems": subitems,
        }

    @staticmethod
    def get_task_status(board_data: dict, task_id: str) -> str | None:
        """
        Find a task by its ID in the given board data and return its status.
        Args:
            board_data: The dict returned by get_board_data()
            task_id: The Monday item ID of the task to look up
        Returns:
            The status string (e.g., "Working on it", "Done"), or None
            if the task isn't found or has no status set.
        """
        task_id = str(task_id)  # normalize in case caller passed an int
        for group_data in board_data.values():
            for task in group_data["tasks"]:
                if task["id"] == task_id:
                    return task["columns"].get("project_status")
        return None

    @staticmethod
    def get_target_subtask_(task_data: dict) -> dict | None:
        """
        Find the first subtask to work on for a main task that is 'Working on it'.
        Args:
            task_data: The dict returned by get_task_data().
        Returns:
            The first subtask dict that satisfies one of these rules (in order):
              1. It is the first subitem and its status is 'Not Started'.
              2. The previous subitem is 'Done' and this subitem is 'Not Started'.
            Returns None if the parent task is not 'Working on it', or no
            subitem matches the above rules.
        """
        # guard to double check if the main task is 'Working on it'
        if task_data["columns"].get("project_status") != "Working on it":
            return None
        
        subitems = task_data.get("subitems") or []
        for i, subitem in enumerate(subitems):
            if subitem["columns"].get("status") != "Not Started":
                continue
            if i == 0 or subitems[i - 1]["columns"].get("status") == "Done":
                return subitem

        return None


if __name__ == "__main__":
    client = Monday(
        token=os.getenv("MONDAY_API_TOKEN"),
        board_id=int(os.getenv("MONDAY_BOARD_ID")),
    )
    # --- test get_board_summary ---
    summary = client.get_board_summary()
    print(json.dumps(summary, indent=2))
    # --- test get_board_data ---
    data = client.get_board_data()
    print(json.dumps(data, indent=2))
    first_group = next(iter(data.values()))
    if first_group["tasks"]:
        test_task_id = first_group["tasks"][0]["id"]
        # --- test get_task_data ---
        print(f"\nFetching task data for task id: {test_task_id}")
        task_data = client.get_task_data(test_task_id)
        print(json.dumps(task_data, indent=2))
        # --- test get_task_status ---
        status = Monday.get_task_status(data, test_task_id)
        print(f"\nStatus for task {test_task_id}: {status!r}")
        status_missing = Monday.get_task_status(data, "nonexistent_id")
        print(f"Status for nonexistent task: {status_missing!r}")  # expected: None
    else:
        print("No tasks found on the board to test get_task_data / get_task_status.")
