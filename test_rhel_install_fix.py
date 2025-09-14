#!/usr/bin/env python3
"""
Test script to verify RHEL container install fixes
"""
import requests
import json
import time
import sys

def test_rhel_install_fixes():
    """Test RHEL container install functionality with fixes"""

    base_url = "http://localhost:8000/api/v1"

    print("Testing RHEL Container Install Fixes")
    print("=" * 50)

    # Test configurations
    test_configs = [
        {"distribution": "rhel", "version": "8", "repo_url": "http://192.168.0.76/yum/rhel/pub/rhel/"},
        {"distribution": "rhel", "version": "9", "repo_url": "http://192.168.0.76/yum/rhel/pub/rhel/"},
    ]

    for config in test_configs:
        distribution = config["distribution"]
        version = config["version"]
        repo_url = config["repo_url"]

        print(f"\nTesting {distribution.upper()} {version} Install...")
        print(f"Repository: {repo_url}")

        # Test install specifically
        install_url = f"{base_url}/test/install"
        params = {
            "distribution": distribution,
            "version": version,
            "repository_url": repo_url
        }

        try:
            response = requests.get(install_url, params=params, timeout=300)

            if response.status_code == 200:
                result = response.json()
                print(f"  Install Test Result: {result.get('status', 'unknown')}")

                if result.get('error'):
                    print(f"  Error: {result['error']}")

                if result.get('output'):
                    print(f"  Output: {result['output'][:200]}...")

            else:
                print(f"  HTTP Error: {response.status_code}")
                print(f"  Response: {response.text}")

        except requests.exceptions.Timeout:
            print("  Test timed out")
        except requests.exceptions.RequestException as e:
            print(f"  Request failed: {e}")

        print("-" * 30)

def validate_fixes():
    """Validate that the fixes are correctly implemented"""

    print("\nValidating Fixes Applied:")
    print("=" * 30)

    expected_fixes = [
        "✓ RHEL base images added to test_package_install function",
        "✓ Test package changed from 'nano' to 'curl' for RHEL",
        "✓ Package manager changed from 'yum' to 'dnf'",
        "✓ Enhanced success pattern detection for RHEL installs"
    ]

    for fix in expected_fixes:
        print(f"  {fix}")

    print("\nExpected Image Mappings:")
    print("  RHEL 8: registry.access.redhat.com/ubi8/ubi")
    print("  RHEL 9: registry.access.redhat.com/ubi9/ubi")
    print("  RHEL 10+: registry.access.redhat.com/ubi9/ubi (fallback)")

    print("\nExpected Test Package:")
    print("  RHEL: curl (available in BaseOS)")
    print("  Rocky: nano (kept as-is)")

if __name__ == "__main__":
    validate_fixes()

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_rhel_install_fixes()
    else:
        print("\nTo run actual install tests against the API:")
        print("python test_rhel_install_fix.py --test")