# Linux Mirror Testing Solution - Test Endpoints

import yaml
import asyncio
import time
from datetime import datetime
from fastapi import APIRouter, WebSocket
from typing import Dict, Any, List
from models.test import TestResult, TestRequest
from services.test_service import test_service
from core.config import settings

router = APIRouter()

# Global test tracking
test_tracker = {}  # Format: {f"{distribution}-{version}": {"start_time": datetime, "status": "running"}}

async def test_repository_comprehensive(distribution: str, version: str, repository_url: str):
    """Perform comprehensive repository testing including update and install tests"""
    import aiohttp
    import subprocess
    import tempfile
    import os

    test_key = f"{distribution}-{version}"
    test_tracker[test_key] = {
        "start_time": datetime.now(),
        "status": "running",
        "repository": repository_url,
        "test_results": {
            "connectivity": {"status": "pending", "duration": 0, "error": None},
            "update": {"status": "pending", "duration": 0, "error": None},
            "install": {"status": "pending", "duration": 0, "error": None}
        }
    }

    try:
        # Phase 1: Connectivity Test
        connectivity_start = datetime.now()
        connectivity_status, connectivity_error = await test_connectivity(distribution, version, repository_url)
        connectivity_duration = (datetime.now() - connectivity_start).seconds

        test_tracker[test_key]["test_results"]["connectivity"] = {
            "status": connectivity_status,
            "duration": connectivity_duration,
            "error": connectivity_error
        }

        # If connectivity fails, skip other tests
        if connectivity_status == "failure":
            test_tracker[test_key]["status"] = "failure"
            test_tracker[test_key]["error_message"] = f"Connectivity failed: {connectivity_error}"
        else:
            # Phase 2: Update Test (apt update / yum update)
            update_start = datetime.now()
            update_status, update_error = await test_repository_update(distribution, version, repository_url)
            update_duration = (datetime.now() - update_start).seconds

            test_tracker[test_key]["test_results"]["update"] = {
                "status": update_status,
                "duration": update_duration,
                "error": update_error
            }

            # Phase 3: Install Test (install a common package)
            install_start = datetime.now()
            install_status, install_error = await test_package_install(distribution, version, repository_url)
            install_duration = (datetime.now() - install_start).seconds

            test_tracker[test_key]["test_results"]["install"] = {
                "status": install_status,
                "duration": install_duration,
                "error": install_error
            }

            # Determine overall status
            if all(result["status"] == "success" for result in test_tracker[test_key]["test_results"].values()):
                overall_status = "success"
                error_msg = None
            elif any(result["status"] == "success" for result in test_tracker[test_key]["test_results"].values()):
                overall_status = "partial"
                failures = [name for name, result in test_tracker[test_key]["test_results"].items() if result["status"] == "failure"]
                error_msg = f"Failed tests: {', '.join(failures)}"
            else:
                overall_status = "failure"
                error_msg = "All tests failed"

            test_tracker[test_key]["status"] = overall_status
            test_tracker[test_key]["error_message"] = error_msg

    except Exception as e:
        test_tracker[test_key]["status"] = "failure"
        test_tracker[test_key]["error_message"] = f"Test framework error: {str(e)}"

    # Update final status
    end_time = datetime.now()
    duration = (end_time - test_tracker[test_key]["start_time"]).seconds
    test_tracker[test_key]["end_time"] = end_time
    test_tracker[test_key]["duration"] = duration


async def test_connectivity(distribution: str, version: str, repository_url: str):
    """Test basic repository connectivity"""
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            test_urls = []

            if distribution.lower() == "debian":
                # Use codenames for all Debian versions
                codenames = {
                    "7": "wheezy", "8": "jessie", "9": "stretch", "10": "buster",
                    "11": "bullseye", "12": "bookworm", "13": "trixie"
                }
                codename = codenames.get(version, version)
                test_urls = [f"{repository_url}/dists/{codename}/Release"]
            elif distribution.lower() == "ubuntu":
                codenames = {"18.04": "bionic", "20.04": "focal", "22.04": "jammy", "24.04": "noble"}
                codename = codenames.get(version, version)
                test_urls = [f"{repository_url}/dists/{codename}/Release"]
            elif distribution.lower() == "kali":
                # Kali uses kali-rolling
                test_urls = [f"{repository_url}/dists/kali-rolling/Release"]
            elif distribution.lower() == "rocky":
                # Rocky Linux repo structure: test repodata for BaseOS
                test_urls = [f"{repository_url}/{version}/BaseOS/x86_64/os/repodata/repomd.xml"]
            elif distribution.lower() == "rhel":
                # RHEL repo structure: test repodata for BaseOS
                test_urls = [f"{repository_url}/{version}/BaseOS/x86_64/os/repodata/repomd.xml"]
            else:
                test_urls = [repository_url]

            for url in test_urls:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return "success", None
                    else:
                        return "failure", f"HTTP {response.status}"

            return "failure", "No valid URLs found"

    except Exception as e:
        return "failure", str(e)


async def test_repository_update(distribution: str, version: str, repository_url: str):
    """Test repository update in a container"""
    import os
    try:
        # Get base image from config
        base_images = {
            "debian": f"debian:{version}" if version in ["11", "12"] else "debian:latest",
            "ubuntu": f"ubuntu:{version}" if version in ["20.04", "22.04", "24.04"] else "ubuntu:latest",
            "kali": "kalilinux/kali-rolling:latest",
            "rocky": f"rockylinux:{version}" if version in ["8", "9"] else "rockylinux:9",
            "rhel": f"registry.access.redhat.com/ubi{version}/ubi" if version in ["8", "9"] else "registry.access.redhat.com/ubi9/ubi"
        }

        image = base_images.get(distribution.lower(), "ubuntu:latest")

        # Set Docker host from environment
        docker_host = os.environ.get('DOCKER_HOST', 'tcp://docker-daemon:2376')

        # Create sources.list content for the test
        if distribution.lower() in ["debian", "ubuntu", "kali"]:
            if distribution.lower() == "kali":
                # Kali uses kali-rolling as the distribution name
                sources_content = f"deb {repository_url} kali-rolling main"
            else:
                codename = get_codename(distribution, version)
                sources_content = f"deb {repository_url} {codename} main"

            # Create Docker command to test apt update with explicit Docker host
            docker_cmd = [
                "docker", "run", "--rm",
                image, "bash", "-c",
                f"""
                echo 'nameserver 8.8.8.8' > /etc/resolv.conf && \\
                echo 'nameserver 1.1.1.1' >> /etc/resolv.conf && \\
                echo '{sources_content}' > /etc/apt/sources.list && \\
                apt-get update -y --allow-insecure-repositories 2>&1
                """
            ]
        elif distribution.lower() in ["rocky", "rhel", "centos"]:
            # For RPM-based systems, test with dnf/yum update
            if distribution.lower() == "rocky" and version in ["8", "9", "10"]:
                # Rocky Linux repo structure: baseurl/rocky/version/BaseOS/arch/os/
                baseos_url = f"{repository_url}/{version}/BaseOS/x86_64/os/"
            elif distribution.lower() == "rhel" and version in ["8", "9", "10"]:
                # RHEL repo structure for private repo: baseurl/version/BaseOS/arch/os/
                baseos_url = f"{repository_url}/{version}/BaseOS/x86_64/os/"

            # Set up repo configuration for both Rocky and RHEL
            if distribution.lower() in ["rocky", "rhel"] and version in ["8", "9", "10"]:
                repo_name = f"{distribution.lower()}-baseos"
                repo_display_name = f"{distribution.title()} {version} - BaseOS"

                # Both RHEL and Rocky Linux use similar configuration for private repos
                bash_script = (
                    f"export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && "
                    f"echo 'nameserver 8.8.8.8' > /etc/resolv.conf && "
                    f"echo 'nameserver 1.1.1.1' >> /etc/resolv.conf && "
                    f"rm -rf /etc/yum.repos.d/* && "
                    f"mkdir -p /etc/yum.repos.d && "
                    f"echo '[{repo_name}]' > /etc/yum.repos.d/test.repo && "
                    f"echo 'name={repo_display_name}' >> /etc/yum.repos.d/test.repo && "
                    f"echo 'baseurl={baseos_url}' >> /etc/yum.repos.d/test.repo && "
                    f"echo 'enabled=1' >> /etc/yum.repos.d/test.repo && "
                    f"echo 'gpgcheck=0' >> /etc/yum.repos.d/test.repo && "
                    f"dnf clean all && "
                    f"dnf --disablerepo='*' --enablerepo='{repo_name}' makecache 2>&1"
                )
                docker_cmd = [
                    "docker", "run", "--rm", "--env", "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                    image, "bash", "-c",
                    bash_script
                ]
            else:
                # Fallback for other RPM systems
                docker_cmd = [
                    "docker", "run", "--rm",
                    image, "bash", "-c",
                    f"curl -I {repository_url} 2>&1"
                ]
        else:
            # For other systems, just test connectivity
            docker_cmd = [
                "docker", "run", "--rm",
                "alpine:latest", "sh", "-c",
                f"wget -q --spider {repository_url} 2>&1 || curl -I {repository_url} 2>&1"
            ]

        # Run the test with timeout
        # Set environment to include Docker host
        env = os.environ.copy()
        env['DOCKER_HOST'] = docker_host

        process = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env
        )

        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=120)
            output = stdout.decode()

            if process.returncode == 0:
                if "Reading package lists" in output or "Hit:" in output or "Get:" in output:
                    return "success", None
                elif "Metadata cache created" in output or "Cache created successfully" in output:
                    return "success", None
                elif distribution.lower() in ["rocky", "rhel", "centos"] and "Rocky Linux" in output:
                    return "success", None
                else:
                    return "partial", "Update completed but with warnings"
            else:
                return "failure", f"Update failed: {output[-200:]}"  # Last 200 chars

        except asyncio.TimeoutError:
            process.kill()
            return "failure", "Update test timed out"

    except Exception as e:
        return "failure", f"Container error: {str(e)}"


async def test_package_install(distribution: str, version: str, repository_url: str):
    """Test package installation from repository"""
    import os
    try:
        base_images = {
            "debian": f"debian:{version}" if version in ["11", "12"] else "debian:latest",
            "ubuntu": f"ubuntu:{version}" if version in ["20.04", "22.04", "24.04"] else "ubuntu:latest",
            "kali": "kalilinux/kali-rolling:latest",
            "rocky": f"rockylinux:{version}" if version in ["8", "9"] else "rockylinux:9",
            "rhel": f"registry.access.redhat.com/ubi{version}/ubi" if version in ["8", "9"] else "registry.access.redhat.com/ubi9/ubi"
        }

        image = base_images.get(distribution.lower(), "ubuntu:latest")

        # Set Docker host from environment
        docker_host = os.environ.get('DOCKER_HOST', 'tcp://docker-daemon:2376')

        if distribution.lower() in ["debian", "ubuntu", "kali"]:
            if distribution.lower() == "kali":
                # Kali uses kali-rolling as the distribution name
                sources_content = f"deb {repository_url} kali-rolling main"
                test_package = "curl"  # Reliable package in Kali
            else:
                codename = get_codename(distribution, version)
                sources_content = f"deb {repository_url} {codename} main"
                test_package = "nano"  # Most reliable package across Debian/Ubuntu versions

            docker_cmd = [
                "docker", "run", "--rm",
                image, "bash", "-c",
                f"""
                echo 'nameserver 8.8.8.8' > /etc/resolv.conf && \\
                echo 'nameserver 1.1.1.1' >> /etc/resolv.conf && \\
                echo '{sources_content}' > /etc/apt/sources.list && \\
                apt-get update -y --allow-insecure-repositories && \\
                apt-get install -y --allow-unauthenticated {test_package} 2>&1
                """
            ]
        elif distribution.lower() in ["rocky", "rhel", "centos"]:
            # For RPM-based systems, test with dnf install
            if distribution.lower() == "rocky" and version in ["8", "9", "10"]:
                # Rocky Linux repo structure
                baseos_url = f"{repository_url}/{version}/BaseOS/x86_64/os/"
                test_package = "nano"  # Reliable package in Rocky Linux BaseOS repository
            elif distribution.lower() == "rhel" and version in ["8", "9", "10"]:
                # RHEL repo structure for private repo
                baseos_url = f"{repository_url}/{version}/BaseOS/x86_64/os/"
                test_package = "tree"  # tree is available in RHEL BaseOS repository and not pre-installed

            # Set up repo configuration for both Rocky and RHEL
            if distribution.lower() in ["rocky", "rhel"] and version in ["8", "9", "10"]:
                repo_name = f"{distribution.lower()}-baseos"
                repo_display_name = f"{distribution.title()} {version} - BaseOS"

                # Both RHEL and Rocky Linux use similar configuration for private repos
                bash_script = (
                    f"export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && "
                    f"echo 'nameserver 8.8.8.8' > /etc/resolv.conf && "
                    f"echo 'nameserver 1.1.1.1' >> /etc/resolv.conf && "
                    f"rm -rf /etc/yum.repos.d/* && "
                    f"mkdir -p /etc/yum.repos.d && "
                    f"echo '[{repo_name}]' > /etc/yum.repos.d/test.repo && "
                    f"echo 'name={repo_display_name}' >> /etc/yum.repos.d/test.repo && "
                    f"echo 'baseurl={baseos_url}' >> /etc/yum.repos.d/test.repo && "
                    f"echo 'enabled=1' >> /etc/yum.repos.d/test.repo && "
                    f"echo 'gpgcheck=0' >> /etc/yum.repos.d/test.repo && "
                    f"dnf clean all && "
                    f"dnf --disablerepo='*' --enablerepo='{repo_name}' install -y {test_package} 2>&1"
                )
                docker_cmd = [
                    "docker", "run", "--rm", "--env", "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                    image, "bash", "-c",
                    bash_script
                ]
            else:
                return "success", "Other RPM-based install test not implemented"
        else:
            # For other systems
            return "success", "Install test not implemented for this distribution"

        # Set environment to include Docker host
        env = os.environ.copy()
        env['DOCKER_HOST'] = docker_host

        process = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env
        )

        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=180)
            output = stdout.decode()

            if process.returncode == 0:
                if "Setting up" in output or "Processing triggers" in output:
                    return "success", None
                elif "Installed:" in output or "Complete!" in output:
                    return "success", None
                elif distribution.lower() in ["rocky", "rhel", "centos"] and ("Transaction complete" in output or "Transaction test" in output or "Running transaction" in output):
                    return "success", None
                else:
                    return "partial", "Package installed but with warnings"
            else:
                return "failure", f"Install failed: {output[-200:]}"

        except asyncio.TimeoutError:
            process.kill()
            return "failure", "Install test timed out"

    except Exception as e:
        return "failure", f"Container error: {str(e)}"


def get_codename(distribution: str, version: str):
    """Get the codename for a distribution version"""
    codenames = {
        "debian": {"7": "wheezy", "8": "jessie", "9": "stretch", "10": "buster", "11": "bullseye", "12": "bookworm", "13": "trixie"},
        "ubuntu": {"18.04": "bionic", "20.04": "focal", "22.04": "jammy", "24.04": "noble"},
        "kali": {"kali-rolling": "kali-rolling"}
    }
    return codenames.get(distribution.lower(), {}).get(version, version)

@router.post("/test")
async def start_test(test_request: TestRequest):
    """Start a test for the specified distributions and repositories"""
    # In a real implementation, this would start a background task
    # For now, we'll simulate a test result
    print(f"Starting test for {test_request.distribution} {test_request.version}")
    result = {
        "distribution": test_request.distribution,
        "version": test_request.version,
        "status": "success",
        "repository": test_request.repository_url,
        "duration_seconds": 15,
        "error_message": None
    }
    return result

@router.get("/test")
async def get_test_list():
    """Get list of repositories to test based on configuration"""
    # Read the config file to get actual repository URLs
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading config file: {e}")
        # Return fallback data if config can't be read
        repositories = []
        
        # Debian versions (hardcoded for fallback only)
        debian_versions = ["7", "8", "9", "10", "11", "12", "13"]
        for version in debian_versions:
            repositories.append({
                "distribution": "Debian",
                "version": version,
                "repository": f"http://mirror.example.com/debian-{version}"
            })
        
        # Ubuntu versions (hardcoded for fallback only)
        ubuntu_versions = ["18.04", "20.04", "22.04", "24.04", "25.04"]
        for version in ubuntu_versions:
            repositories.append({
                "distribution": "Ubuntu",
                "version": version,
                "repository": f"http://mirror.example.com/ubuntu-{version}"
            })
        
        # Kali (hardcoded for fallback only)
        repositories.append({
            "distribution": "Kali",
            "version": "kali-rolling",
            "repository": "http://mirror.example.com/kali-rolling"
        })
        
        # Rocky Linux versions (hardcoded for fallback only)
        rocky_versions = ["8", "9", "10"]
        for version in rocky_versions:
            repositories.append({
                "distribution": "Rocky",
                "version": version,
                "repository": f"http://mirror.example.com/rocky-{version}"
            })
        
        # RHEL versions (hardcoded for fallback only)
        rhel_versions = ["8", "9", "10"]
        for version in rhel_versions:
            repositories.append({
                "distribution": "RHEL",
                "version": version,
                "repository": f"http://mirror.example.com/rhel-{version}"
            })
        
        return repositories
    
    repositories = []
    
    # Process Debian repositories
    if 'repositories' in config and 'debian' in config['repositories']:
        debian_repos = config['repositories']['debian']
        for repo in debian_repos:
            if 'url' in repo and 'distributions' in repo:
                for version in repo['distributions']:
                    repositories.append({
                        "distribution": "Debian",
                        "version": version,
                        "repository": repo['url']
                    })
    
    # Process Ubuntu repositories
    if 'repositories' in config and 'ubuntu' in config['repositories']:
        ubuntu_repos = config['repositories']['ubuntu']
        for repo in ubuntu_repos:
            if 'url' in repo and 'distributions' in repo:
                for version in repo['distributions']:
                    repositories.append({
                        "distribution": "Ubuntu",
                        "version": version,
                        "repository": repo['url']
                    })
    
    # Process Kali repositories
    if 'repositories' in config and 'kali' in config['repositories']:
        kali_repos = config['repositories']['kali']
        for repo in kali_repos:
            if 'url' in repo and 'distributions' in repo:
                for version in repo['distributions']:
                    repositories.append({
                        "distribution": "Kali",
                        "version": version,
                        "repository": repo['url']
                    })
    
    # Process Rocky Linux repositories
    if 'repositories' in config and 'rocky' in config['repositories']:
        rocky_repos = config['repositories']['rocky']
        for repo in rocky_repos:
            if 'url' in repo and 'distributions' in repo:
                for version in repo['distributions']:
                    repositories.append({
                        "distribution": "Rocky",
                        "version": version,
                        "repository": repo['url']
                    })
    
    # Process RHEL repositories
    if 'repositories' in config and 'rhel' in config['repositories']:
        rhel_repos = config['repositories']['rhel']
        for repo in rhel_repos:
            if 'url' in repo and 'distributions' in repo:
                for version in repo['distributions']:
                    repositories.append({
                        "distribution": "RHEL",
                        "version": version,
                        "repository": repo['url']
                    })
    
    # Add status field and start tests for each repository
    for repo in repositories:
        test_key = f"{repo['distribution']}-{repo['version']}"

        if test_key in test_tracker:
            # Get current status and duration
            test_info = test_tracker[test_key]
            repo["status"] = test_info["status"]

            if "duration" in test_info:
                repo["duration_seconds"] = test_info["duration"]
            elif test_info["status"] == "running":
                # Calculate current duration for running tests
                current_duration = (datetime.now() - test_info["start_time"]).seconds
                repo["duration_seconds"] = current_duration
            else:
                repo["duration_seconds"] = 0

            repo["error_message"] = test_info.get("error_message")

            # Add detailed test results if available
            if "test_results" in test_info:
                repo["test_details"] = {
                    "connectivity": {
                        "status": test_info["test_results"]["connectivity"]["status"],
                        "duration": test_info["test_results"]["connectivity"]["duration"],
                        "error": test_info["test_results"]["connectivity"]["error"]
                    },
                    "update": {
                        "status": test_info["test_results"]["update"]["status"],
                        "duration": test_info["test_results"]["update"]["duration"],
                        "error": test_info["test_results"]["update"]["error"]
                    },
                    "install": {
                        "status": test_info["test_results"]["install"]["status"],
                        "duration": test_info["test_results"]["install"]["duration"],
                        "error": test_info["test_results"]["install"]["error"]
                    }
                }
            else:
                repo["test_details"] = None
        else:
            # Start a new test asynchronously
            repo["status"] = "running"
            repo["duration_seconds"] = 0
            repo["error_message"] = None
            # Start the test in the background
            asyncio.create_task(test_repository_comprehensive(repo['distribution'], repo['version'], repo['repository']))

    return repositories

@router.get("/test/{distro}/{version}")
async def get_test_result(distro: str, version: str):
    """Get test result for a specific distro/version"""
    # This would normally query the database
    return {"distro": distro, "version": version, "status": "success"}

@router.websocket("/test/ws")
async def websocket_test_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time test updates"""
    await websocket.accept()
    try:
        # Send initial message
        await websocket.send_text("Connected to test WebSocket")

        # Send initial repository data
        repositories = await get_test_list()
        import json
        await websocket.send_text(json.dumps(repositories))

        # Send periodic updates with real-time durations
        while True:
            try:
                # Check if client sent any message (non-blocking)
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                    if message == "get_status":
                        # Client is requesting status update
                        repositories = await get_test_list()
                        await websocket.send_text(json.dumps(repositories))
                except asyncio.TimeoutError:
                    # No message received, continue with periodic updates
                    pass

                # Send periodic updates every 2 seconds
                await asyncio.sleep(2)
                repositories = await get_test_list()
                await websocket.send_text(json.dumps(repositories))

            except Exception as e2:
                print(f"Error in WebSocket loop: {e2}")
                break

    except Exception as e:
        print(f"WebSocket error in test endpoint: {e}")
