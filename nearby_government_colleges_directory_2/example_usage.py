#!/usr/bin/env python3
"""
Example usage of the Government College Locator application.
This script demonstrates how to use the CollegeLocator class programmatically.
"""

from college_locator import CollegeLocator

def example_usage():
    """Example of how to use the CollegeLocator class."""
    
    # Initialize the locator
    locator = CollegeLocator()
    
    # Example 1: Search for colleges in Bhopal, India
    print("Example 1: Searching for colleges in Bhopal, India")
    print("-" * 50)
    locator.find_colleges("Bhopal, India", radius=10000)  # 10 km radius
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: Search for colleges in Delhi, India
    print("Example 2: Searching for colleges in Delhi, India")
    print("-" * 50)
    locator.find_colleges("Delhi, India", radius=15000)  # 15 km radius
    
    print("\n" + "="*60 + "\n")
    
    # Example 3: Search for colleges in Mumbai, India
    print("Example 3: Searching for colleges in Mumbai, India")
    print("-" * 50)
    locator.find_colleges("Mumbai, India", radius=20000)  # 20 km radius

if __name__ == "__main__":
    example_usage()
