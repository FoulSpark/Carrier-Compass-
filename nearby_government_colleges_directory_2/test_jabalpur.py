#!/usr/bin/env python3
"""
Test script to verify the fixes for Jabalpur search and live location detection.
"""

from college_locator import CollegeLocator

def test_jabalpur_search():
    """Test Jabalpur search with 100km radius"""
    print("🧪 Testing Jabalpur search with 100km radius...")
    print("=" * 50)
    
    locator = CollegeLocator()
    
    # Test Jabalpur search
    print("\n1. Testing Jabalpur geocoding...")
    coords = locator.get_coordinates("Jabalpur")
    if coords:
        lat, lon = coords
        print(f"✅ Jabalpur coordinates found: {lat:.6f}, {lon:.6f}")
        
        # Test with 100km radius
        print(f"\n2. Testing college search with 100km radius...")
        colleges = locator.get_nearby_colleges(lat, lon, 100000)  # 100km in meters
        print(f"Found {len(colleges)} colleges")
        
        if colleges:
            print("\n📋 College details:")
            for i, college in enumerate(colleges[:5], 1):  # Show first 5
                print(f"{i}. {college['name']} - {college['operator']}")
        else:
            print("❌ No colleges found. This might indicate an issue with the search.")
    else:
        print("❌ Could not find Jabalpur coordinates")

def test_live_location():
    """Test live location detection"""
    print("\n🧪 Testing live location detection...")
    print("=" * 50)
    
    locator = CollegeLocator()
    live_data = locator.get_live_location()
    
    if live_data:
        lat, lon, location_name = live_data
        print(f"✅ Live location detected: {location_name}")
        print(f"Coordinates: {lat:.6f}, {lon:.6f}")
        
        # Check if it's detecting Jabalpur correctly
        if "jabalpur" in location_name.lower():
            print("✅ Correctly detected Jabalpur!")
        else:
            print(f"⚠️  Detected {location_name} instead of Jabalpur")
    else:
        print("❌ Could not detect live location")

if __name__ == "__main__":
    print("🏛️  TESTING COLLEGE LOCATOR FIXES 🏛️")
    print("=" * 60)
    
    test_live_location()
    test_jabalpur_search()
    
    print("\n" + "=" * 60)
    print("✅ Testing completed!")
