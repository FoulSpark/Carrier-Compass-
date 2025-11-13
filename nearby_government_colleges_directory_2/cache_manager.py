#!/usr/bin/env python3
"""
Cache Manager Script for College Directory
This script provides utilities to manage the college cache system.
"""

import sys
import os
from college_cache import CollegeCache

def main():
    """Main function to handle command line arguments."""
    cache = CollegeCache()
    
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'populate':
        print("🔄 Populating cache with sample data...")
        cache.populate_sample_cache()
        stats = cache.get_cache_stats()
        print(f"✅ Cache populated. Total locations: {stats['total_cached_locations']}, Total colleges: {stats['total_cached_colleges']}")
        
    elif command == 'stats':
        print_stats(cache)
        
    elif command == 'search':
        if len(sys.argv) < 3:
            print("❌ Please provide a search query")
            print("Usage: python cache_manager.py search <query> [stream]")
            return
        
        query = sys.argv[2]
        stream = sys.argv[3] if len(sys.argv) > 3 else 'all'
        
        colleges = cache.search_cached_colleges(query, stream)
        print(f"\n🔍 Search results for '{query}' (stream: {stream}):")
        print(f"Found {len(colleges)} colleges in cache:")
        
        for i, college in enumerate(colleges, 1):
            cached_location = college.get('cached_location', 'Unknown')
            print(f"{i}. {college['name']} - {cached_location}")
            
    elif command == 'locations':
        locations = cache.get_cached_locations()
        print(f"\n🏙️ Cached locations ({len(locations)} total):")
        for i, location in enumerate(locations, 1):
            print(f"{i}. {location['location_name']} - {location['college_count']} colleges (accessed {location['access_count']} times)")
            
    elif command == 'clear':
        confirm = input("⚠️ Are you sure you want to clear all cache data? (yes/no): ")
        if confirm.lower() == 'yes':
            cache.clear_cache()
            print("✅ Cache cleared")
        else:
            print("❌ Operation cancelled")
            
    elif command == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        removed_count = cache.clear_expired_cache(days)
        print(f"✅ Removed {removed_count} expired cache entries older than {days} days")
        
    elif command == 'test':
        test_cache_functionality(cache)
        
    else:
        print(f"❌ Unknown command: {command}")
        print_help()

def print_stats(cache):
    """Print cache statistics."""
    stats = cache.get_cache_stats()
    
    print("\n📊 Cache Statistics:")
    print(f"  Total Cached Locations: {stats['total_cached_locations']}")
    print(f"  Total Cached Colleges: {stats['total_cached_colleges']}")
    print(f"  Total Accesses: {stats['total_accesses']}")
    print(f"  Most Popular Location: {stats['most_popular_location']} ({stats['most_popular_access_count']} accesses)")
    print(f"  Cache File Size: {stats['cache_file_size']} bytes")
    
    locations = cache.get_cached_locations()
    if locations:
        print(f"\n🏆 Top 5 Most Accessed Locations:")
        for i, location in enumerate(locations[:5], 1):
            print(f"  {i}. {location['location_name']}: {location['access_count']} accesses, {location['college_count']} colleges")

def test_cache_functionality(cache):
    """Test cache functionality with sample searches."""
    print("\n🧪 Testing cache functionality...")
    
    # Test 1: Search for Jabalpur
    print("\n1. Testing Jabalpur search...")
    colleges = cache.get_cached_colleges(23.1815, 79.9864, 10000, "all", "Jabalpur")
    if colleges:
        print(f"✅ Found {len(colleges)} colleges for Jabalpur")
    else:
        print("❌ No colleges found for Jabalpur")
    
    # Test 2: Search cached colleges
    print("\n2. Testing search functionality...")
    search_results = cache.search_cached_colleges("Engineering", "all")
    print(f"✅ Found {len(search_results)} engineering colleges in cache")
    
    # Test 3: Get locations
    print("\n3. Testing locations list...")
    locations = cache.get_cached_locations()
    print(f"✅ Found {len(locations)} cached locations")
    
    # Test 4: Get stats
    print("\n4. Testing statistics...")
    stats = cache.get_cache_stats()
    print(f"✅ Cache contains {stats['total_cached_colleges']} colleges across {stats['total_cached_locations']} locations")
    
    print("\n🎉 All tests completed!")

def print_help():
    """Print help information."""
    print("""
🎓 College Cache Manager

Usage: python cache_manager.py <command> [arguments]

Commands:
  populate                      Populate cache with sample data
  stats                         Show cache statistics
  search <query> [stream]       Search colleges in cache
  locations                     List all cached locations
  clear                         Clear all cache data
  cleanup [days]                Remove expired cache entries (default: 7 days)
  test                          Test cache functionality
  help                          Show this help message

Examples:
  python cache_manager.py populate
  python cache_manager.py search "Jabalpur" pcm
  python cache_manager.py locations
  python cache_manager.py cleanup 14
  python cache_manager.py stats
""")

if __name__ == '__main__':
    main()
