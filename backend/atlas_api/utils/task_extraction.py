import re
from typing import List, Dict

def extract_tasks_from_markdown(markdown_content: str) -> List[Dict]:
    """
    Parses markdown content and extracts task items (checkboxes).
    Task items are expected to be in the format:
    - [ ] Task description (for incomplete tasks)
    - [x] Task description (for complete tasks)
    - [X] Task description (for complete tasks, case-insensitive)

    Args:
        markdown_content: The string content of the markdown note.

    Returns:
        A list of dictionaries, where each dictionary represents a task
        with 'description' and 'status' (either 'todo' or 'done').
    """
    tasks = []
    # Regex to find lines starting with '- [ ] ' or '- [x] ' or '- [X] '
    # It captures the checkbox status and the task description.
    task_pattern = re.compile(r"^[ \t]*- \[(?P<status>[xX\s])\] (?P<description>.*)", re.MULTILINE)

    for match in task_pattern.finditer(markdown_content):
        status_char = match.group('status').strip().lower()
        description = match.group('description').strip()

        status = "done" if status_char == "x" else "todo"
        
        if description: # Only add if description is not empty
            tasks.append({
                "description": description,
                "status": status
            })
            
    return tasks

if __name__ == '__main__':
    # Simple test cases
    test_content_1 = """
# My Note
This is a paragraph.

- [ ] Task one
- [x] Task two is completed
  - [ ] Subtask
- [X] Task three (another completed)

Some more text.
- [ ] Another task
    """
    expected_1 = [
        {"description": "Task one", "status": "todo"},
        {"description": "Task two is completed", "status": "done"},
        {"description": "Subtask", "status": "todo"},
        {"description": "Task three (another completed)", "status": "done"},
        {"description": "Another task", "status": "todo"}
    ]
    result_1 = extract_tasks_from_markdown(test_content_1)
    assert result_1 == expected_1, f"Test 1 failed. Expected: {expected_1}, Got: {result_1}"

    test_content_2 = "No tasks here."
    expected_2 = []
    result_2 = extract_tasks_from_markdown(test_content_2)
    assert result_2 == expected_2, f"Test 2 failed. Expected: {expected_2}, Got: {result_2}"

    test_content_3 = """
- [ ]
- [x] A task with no description
    """
    expected_3 = [
        {"description": "A task with no description", "status": "done"}
    ]
    result_3 = extract_tasks_from_markdown(test_content_3)
    assert result_3 == expected_3, f"Test 3 failed. Expected: {expected_3}, Got: {result_3}"

    print("All task extraction tests passed!")
