import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_step(title):
    print("\n" + "="*20)
    print(title)
    print("="*20)

def call_tool(tool_name, payload):
    url = f"{BASE_URL}/tools/{tool_name}"
    print(f"Calling: {tool_name} with payload: {json.dumps(payload)}")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    try:
        response_json = response.json()
        print(f"Response: {json.dumps(response_json, indent=2)}")
        return response_json
    except json.JSONDecodeError:
        print("Response is not JSON.")
        return None

def main():
    # Step 1: Create a task chain
    print_step("1. Creating Task Chain")
    task_chain_payload = {
        "tasks": [
            {
                "task_id": "TASK-001",
                "description": "Design the database schema",
                "type": "TDD",
                "details": "Define tables for tasks, journal, and project context.",
                "dependencies": []
            },
            {
                "task_id": "TASK-002",
                "description": "Implement the API",
                "type": "CODE",
                "details": "Build the FastAPI server based on the new schema.",
                "dependencies": ["TASK-001"]
            }
        ]
    }
    call_tool("createTaskChain", task_chain_payload)

    # Process tasks until no more are ready
    while True:
        # Step 2: Get the next ready task
        print_step("2. Getting Next Ready Task")
        next_task = call_tool("getNextReadyTask", {})
        
        if not next_task:
            print("\nNo more ready tasks. Workflow complete.")
            break

        task_id = next_task["task_id"]

        # Step 3: Start work on the task
        print_step(f"3. Starting Work on {task_id}")
        call_tool("startWorkOnTask", {"task_id": task_id})

        # Step 4: Get task details
        print_step(f"4. Getting Details for {task_id}")
        call_tool("getTaskDetails", {"task_id": task_id})

        # Step 5: Finish work on the task
        print_step(f"5. Finishing Work on {task_id}")
        call_tool("finishWorkOnTask", {"task_id": task_id})

    # Final verification
    print_step("6. Final Verification")
    print("Checking status of TASK-001...")
    task1_details = call_tool("getTaskDetails", {"task_id": "TASK-001"})
    assert task1_details["status"] == "COMPLETED"
    
    print("\nChecking status of TASK-002...")
    task2_details = call_tool("getTaskDetails", {"task_id": "TASK-002"})
    assert task2_details["status"] == "COMPLETED"
    
    print("\nEnd-to-end test successful!")


if __name__ == "__main__":
    main()