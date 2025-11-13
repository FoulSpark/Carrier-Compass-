#!/usr/bin/env python3
"""
Test script to verify Bhopal college search functionality
"""

import requests
import json

def test_bhopal_search():
    """Test Bhopal search with different streams"""
    base_url = "http://localhost:5002"
    
    test_cases = [
        {"stream": "pcm", "expected_min": 5},
        {"stream": "pcb", "expected_min": 3},
        {"stream": "arts", "expected_min": 5},
        {"stream": "commerce", "expected_min": 4},
        {"stream": "all", "expected_min": 10}
    ]
    
    print("🧪 Testing Bhopal college search functionality...\n")
    
    for test_case in test_cases:
        stream = test_case["stream"]
        expected_min = test_case["expected_min"]
        
        print(f"Testing stream: {stream.upper()}")
        
        payload = {
            "location": "Bhopal",
            "radius": 10,  # 10km
            "stream": stream,
            "use_live_location": False
        }
        
        try:
            response = requests.post(f"{base_url}/api/search", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    colleges = data.get("colleges", [])
                    total_found = len(colleges)
                    source = data.get("source", "unknown")
                    
                    print(f"  ✅ Found {total_found} colleges (source: {source})")
                    
                    if total_found >= expected_min:
                        print(f"  ✅ Expected at least {expected_min}, got {total_found}")
                    else:
                        print(f"  ❌ Expected at least {expected_min}, got {total_found}")
                    
                    # Show first few college names
                    for i, college in enumerate(colleges[:3]):
                        print(f"    {i+1}. {college.get('name', 'Unknown')}")
                    
                    if total_found > 3:
                        print(f"    ... and {total_found - 3} more colleges")
                        
                else:
                    print(f"  ❌ API returned error: {data.get('error', 'Unknown error')}")
                    
            else:
                print(f"  ❌ HTTP Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request failed: {e}")
        
        print()

def test_cache_direct():
    """Test cache functionality directly"""
    print("🔍 Testing cache functionality directly...\n")
    
    try:
        from college_cache import CollegeCache
        cache = CollegeCache()
        
        # Test PCM stream
        colleges = cache.get_cached_colleges(23.2599, 77.4126, 15000, "pcm", "Bhopal")
        if colleges:
            print(f"✅ Cache PCM: Found {len(colleges)} colleges")
            for i, college in enumerate(colleges[:3]):
                print(f"  {i+1}. {college.get('name', 'Unknown')}")
        else:
            print("❌ Cache PCM: No colleges found")
        
        print()
        
        # Test ALL stream
        colleges = cache.get_cached_colleges(23.2599, 77.4126, 15000, "all", "Bhopal")
        if colleges:
            print(f"✅ Cache ALL: Found {len(colleges)} colleges")
            for i, college in enumerate(colleges[:5]):
                print(f"  {i+1}. {college.get('name', 'Unknown')}")
        else:
            print("❌ Cache ALL: No colleges found")
            
    except Exception as e:
        print(f"❌ Cache test failed: {e}")

if __name__ == "__main__":
    test_cache_direct()
    print("-" * 50)
    test_bhopal_search()
