#!/usr/bin/env python
"""Test script to verify RHEL repository connections"""

import requests
import json
import time

def test_rhel_repos():
    """Test RHEL repository connections"""

    base_url = "http://localhost:8000/api/v1"

    print("Testing RHEL Repository Connections")
    print("=" * 50)

    # Get list of repositories
    response = requests.get(f"{base_url}/test/test")

    if response.status_code == 200:
        repos = response.json()

        # Filter for RHEL repositories
        rhel_repos = [repo for repo in repos if repo.get('distribution') == 'RHEL']

        print(f"Found {len(rhel_repos)} RHEL repositories to test:")
        print()

        for repo in rhel_repos:
            print(f"RHEL {repo['version']}:")
            print(f"  Repository: {repo['repository']}")
            print(f"  Status: {repo.get('status', 'pending')}")

            if repo.get('test_details'):
                details = repo['test_details']
                print("  Test Results:")
                print(f"    Connectivity: {details['connectivity']['status']}")
                print(f"    Update Test: {details['update']['status']}")
                print(f"    Install Test: {details['install']['status']}")

            if repo.get('error_message'):
                print(f"  Error: {repo['error_message']}")

            print()
    else:
        print(f"Failed to get repository list: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_rhel_repos()

    print("\nWaiting for tests to complete...")
    time.sleep(10)

    print("\nFinal Results:")
    print("=" * 50)
    test_rhel_repos()