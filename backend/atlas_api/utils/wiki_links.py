import re
from typing import List

def parse_wiki_links(markdown_content: str) -> List[str]:
    """
    Parses markdown content and extracts wiki-links.
    Wiki-links are expected to be in the format [[Link Target]].

    Args:
        markdown_content: The string content of the markdown note.

    Returns:
        A list of strings, where each string is the target of a wiki-link.
        The targets are stripped of leading/trailing whitespace.
    """
    # Regex to find [[...]] patterns. The content inside is captured.
    wiki_link_pattern = re.compile(r'\[\[(.*?)\]\]')
    
    links = []
    for match in wiki_link_pattern.finditer(markdown_content):
        # Extract the captured group (the content inside [[...]])
        link_target = match.group(1).strip()
        if link_target:  # Only add if the target is not empty
            links.append(link_target)
            
    return links

if __name__ == '__main__':
    # Simple test cases
    test_content_1 = "This is a note with a [[Wiki Link]] and another [[Another Link  ]]."
    expected_1 = ["Wiki Link", "Another Link"]
    assert parse_wiki_links(test_content_1) == expected_1, f"Test 1 failed: {parse_wiki_links(test_content_1)}"

    test_content_2 = "No wiki links here."
    expected_2 = []
    assert parse_wiki_links(test_content_2) == expected_2, f"Test 2 failed: {parse_wiki_links(test_content_2)}"

    test_content_3 = "[[Leading and Trailing Spaces]] in link."
    expected_3 = ["Leading and Trailing Spaces"]
    assert parse_wiki_links(test_content_3) == expected_3, f"Test 3 failed: {parse_wiki_links(test_content_3)}"

    test_content_4 = "Multiple [[Same Link]] [[Same Link]] occurrences."
    expected_4 = ["Same Link", "Same Link"]
    assert parse_wiki_links(test_content_4) == expected_4, f"Test 4 failed: {parse_wiki_links(test_content_4)}"
    
    test_content_5 = "[[Empty Link]] but [[Valid Link]]"
    expected_5 = ["Empty Link", "Valid Link"]
    assert parse_wiki_links(test_content_5) == expected_5, f"Test 5 failed: {parse_wiki_links(test_content_5)}"
    
    test_content_6 = "[[  ]] empty link target"
    expected_6 = []
    assert parse_wiki_links(test_content_6) == expected_6, f"Test 6 failed: {parse_wiki_links(test_content_6)}"


    print("All wiki-link parsing tests passed!")
