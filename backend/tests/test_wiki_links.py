import pytest
from atlas_api.utils.wiki_links import parse_wiki_links

def test_parse_wiki_links_basic():
    content = "This is a note with a [[Wiki Link]] and another [[Another Link  ]]."
    expected = ["Wiki Link", "Another Link"]
    assert parse_wiki_links(content) == expected

def test_parse_wiki_links_no_links():
    content = "No wiki links here."
    expected = []
    assert parse_wiki_links(content) == expected

def test_parse_wiki_links_leading_trailing_spaces():
    content = "[[ Leading and Trailing Spaces ]] in link."
    expected = ["Leading and Trailing Spaces"]
    assert parse_wiki_links(content) == expected

def test_parse_wiki_links_multiple_same_links():
    content = "Multiple [[Same Link]] [[Same Link]] occurrences."
    expected = ["Same Link", "Same Link"]
    assert parse_wiki_links(content) == expected

def test_parse_wiki_links_empty_link_target():
    content = "[[ ]] empty link target should be ignored, but [[Valid Link]] should not."
    expected = ["Valid Link"]
    assert parse_wiki_links(content) == expected

def test_parse_wiki_links_special_characters():
    content = "[[Link with Symbols!@#$%^&*()_+=-{}|:\"<>?,./;'[]\\]] and [[Another-Link_with.dots]]"
    expected = ["Link with Symbols!@#$%^&*()_+=-{}|:\"<>?,./;'[]\\", "Another-Link_with.dots"]
    assert parse_wiki_links(content) == expected

def test_parse_wiki_links_multiline():
    content = """
    This is the first line.
    [[Multi
    Line
    Link]] is not supported by current regex, but [[Single Line Link]] is.
    """
    expected = ["Single Line Link"]
    assert parse_wiki_links(content) == expected

def test_parse_wiki_links_nested_brackets():
    # Our regex captures non-greedily, so it should handle this.
    content = "[[Outer [[Inner]] Link]]"
    expected = ["Outer [[Inner"] # This is an expected behavior of the current regex
    assert parse_wiki_links(content) == expected

def test_parse_wiki_links_empty_string():
    content = ""
    expected = []
    assert parse_wiki_links(content) == expected

