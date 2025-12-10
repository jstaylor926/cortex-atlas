import pytest
from atlas_api.utils.task_extraction import extract_tasks_from_markdown

def test_extract_tasks_basic():
    content = """
    - [ ] Task one
    - [x] Task two is completed
    - [X] Task three (another completed)
    """
    expected = [
        {"description": "Task one", "status": "todo"},
        {"description": "Task two is completed", "status": "done"},
        {"description": "Task three (another completed)", "status": "done"}
    ]
    assert extract_tasks_from_markdown(content) == expected

def test_extract_tasks_no_tasks():
    content = "No tasks here."
    expected = []
    assert extract_tasks_from_markdown(content) == expected

def test_extract_tasks_mixed_content():
    content = """
    # My Note
    This is a paragraph.

    - [ ] Task one
    Some more text.
    - [x] Another completed task
    """
    expected = [
        {"description": "Task one", "status": "todo"},
        {"description": "Another completed task", "status": "done"}
    ]
    assert extract_tasks_from_markdown(content) == expected

def test_extract_tasks_empty_description():
    content = """
    - [ ]
    - [x] Valid task
    - [ ] 
    """
    expected = [
        {"description": "Valid task", "status": "done"}
    ]
    assert extract_tasks_from_markdown(content) == expected

def test_extract_tasks_indented():
    content = """
    - [ ] Top level task
      - [x] Indented completed task
        - [ ] Double indented task
    """
    expected = [
        {"description": "Top level task", "status": "todo"},
        {"description": "Indented completed task", "status": "done"},
        {"description": "Double indented task", "status": "todo"}
    ]
    assert extract_tasks_from_markdown(content) == expected

def test_extract_tasks_only_checkbox():
    content = "- [ ]"
    expected = []
    assert extract_tasks_from_markdown(content) == expected

def test_extract_tasks_with_special_chars():
    content = "- [ ] Task with !@#$%^&*()_+=-{}|:\"<>?,./;'[]\\ special chars"
    expected = [
        {"description": "Task with !@#$%^&*()_+=-{}|:\"<>?,./;'[]\\ special chars", "status": "todo"}
    ]
    assert extract_tasks_from_markdown(content) == expected

def test_extract_tasks_empty_string():
    content = ""
    expected = []
    assert extract_tasks_from_markdown(content) == expected
