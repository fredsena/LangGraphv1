#!/usr/bin/env python
"""Test script for the new write_file_to_disk tool."""

from utils.file_tools import write_file_to_disk

# Test the tool directly
result = write_file_to_disk.invoke({
    "file_path": "test_output.txt",
    "content": "This is a test file written to disk by the write_file_to_disk tool!"
})

print(result)
print("\nTest completed successfully!")
