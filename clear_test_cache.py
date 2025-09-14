#!/usr/bin/env python
"""Clear test cache and restart RHEL tests"""

import requests
import time
import subprocess
import signal
import sys
import os

# Function to clear test tracker by restarting backend
def restart_backend():
    print("Restarting backend to clear test cache...")

    # Kill any existing uvicorn processes
    try:
        subprocess.run(['pkill', '-f', 'uvicorn'], check=False)
        subprocess.run(['pkill', '-f', 'main:app'], check=False)
    except:
        pass

    # Wait a moment
    time.sleep(2)

    # Change to backend directory and start server
    backend_dir = os.path.join(os.getcwd(), 'backend')
    os.chdir(backend_dir)

    # Start backend process
    env = os.environ.copy()
    env['PYTHONPATH'] = backend_dir

    # Start in background
    proc = subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 'main:app',
        '--reload', '--host', '0.0.0.0', '--port', '8000'
    ], env=env)

    print(f"Started backend process with PID: {proc.pid}")

    # Wait for server to start
    print("Waiting for backend to start...")
    for i in range(20):
        try:
            response = requests.get('http://localhost:8000/api/v1/test/test', timeout=1)
            if response.status_code == 200:
                print("Backend is running!")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("Backend failed to start")
        return False

    return True

def test_rhel_repos():
    """Test RHEL repository connections"""

    print("Testing RHEL Repository Connections (Fresh)")
    print("=" * 50)

    # Get list of repositories
    response = requests.get("http://localhost:8000/api/v1/test/test")

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

                # Show errors
                if details['install'].get('error'):
                    print(f"    Install Error: {details['install']['error'][:100]}...")

            if repo.get('error_message'):
                print(f"  Error: {repo['error_message']}")

            print()
    else:
        print(f"Failed to get repository list: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    if restart_backend():
        print("Waiting for tests to complete...")
        time.sleep(10)
        test_rhel_repos()
    else:
        print("Failed to restart backend")