#!/usr/bin/env python
"""Test script to verify all repository connections with tree package"""

import requests
import json
import time

def test_all_repos():
    """Test all repository connections"""

    base_url = "http://localhost:8000/api/v1"

    print("Testing All Repository Connections with 'tree' package")
    print("=" * 60)

    # Get list of repositories
    response = requests.get(f"{base_url}/test/test")

    if response.status_code == 200:
        repos = response.json()

        print(f"Found {len(repos)} repositories to test:")
        print()

        # Group by distribution
        distributions = {}
        for repo in repos:
            dist = repo.get('distribution', 'Unknown')
            if dist not in distributions:
                distributions[dist] = []
            distributions[dist].append(repo)

        for dist_name, dist_repos in distributions.items():
            print(f"{dist_name} ({len(dist_repos)} versions):")
            print("-" * 40)

            for repo in dist_repos:
                version = repo.get('version', 'Unknown')
                status = repo.get('status', 'pending')
                print(f"  {dist_name} {version}:")
                print(f"    Repository: {repo['repository']}")
                print(f"    Status: {status}")

                if repo.get('test_details'):
                    details = repo['test_details']
                    print(f"    Tests:")
                    print(f"      Connectivity: {details['connectivity']['status']}")
                    print(f"      Update Test: {details['update']['status']}")
                    print(f"      Install Test: {details['install']['status']}")

                    # Show errors
                    if details['connectivity'].get('error'):
                        print(f"      Connectivity Error: {details['connectivity']['error']}")
                    if details['update'].get('error'):
                        print(f"      Update Error: {details['update']['error']}")
                    if details['install'].get('error'):
                        print(f"      Install Error: {details['install']['error']}")

                if repo.get('error_message'):
                    print(f"    Overall Error: {repo['error_message']}")

                print()
            print()
    else:
        print(f"Failed to get repository list: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_all_repos()