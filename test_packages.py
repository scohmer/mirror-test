#!/usr/bin/env python
"""Test script to verify good packages for each repository type"""

import subprocess
import os

def test_package_availability():
    """Test package availability in different repository types"""

    print("Testing Package Availability Across Repository Types")
    print("=" * 60)

    # Test packages for different repo types
    test_configs = [
        {
            "name": "RHEL 8 BaseOS",
            "image": "registry.access.redhat.com/ubi8/ubi",
            "repo_url": "http://192.168.0.76/yum/rhel/pub/rhel/8/BaseOS/x86_64/os/",
            "packages": ["nano", "rsync", "file", "less", "tar"]
        },
        {
            "name": "RHEL 8 AppStream",
            "image": "registry.access.redhat.com/ubi8/ubi",
            "repo_url": "http://192.168.0.76/yum/rhel/pub/rhel/8/AppStream/x86_64/os/",
            "packages": ["git", "vim", "python3"]
        },
        {
            "name": "Rocky 8 BaseOS",
            "image": "rockylinux:8",
            "repo_url": "http://192.168.0.76/yum/rocky/pub/rocky/8/BaseOS/x86_64/os/",
            "packages": ["nano", "rsync", "file", "less", "curl"]
        },
        {
            "name": "Rocky 8 AppStream",
            "image": "rockylinux:8",
            "repo_url": "http://192.168.0.76/yum/rocky/pub/rocky/8/AppStream/x86_64/os/",
            "packages": ["git", "vim", "httpd"]
        }
    ]

    docker_host = os.environ.get('DOCKER_HOST', 'tcp://docker-daemon:2376')

    for config in test_configs:
        print(f"\n{config['name']}:")
        print("-" * 40)

        repo_name = config['name'].lower().replace(' ', '-')

        setup_script = (
            f"export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && "
            f"rm -rf /etc/yum.repos.d/* && "
            f"mkdir -p /etc/yum.repos.d && "
            f"echo '[{repo_name}]' > /etc/yum.repos.d/test.repo && "
            f"echo 'name={config['name']}' >> /etc/yum.repos.d/test.repo && "
            f"echo 'baseurl={config['repo_url']}' >> /etc/yum.repos.d/test.repo && "
            f"echo 'enabled=1' >> /etc/yum.repos.d/test.repo && "
            f"echo 'gpgcheck=0' >> /etc/yum.repos.d/test.repo && "
            f"/usr/bin/yum clean all > /dev/null 2>&1"
        )

        for package in config['packages']:
            try:
                cmd = [
                    "docker", "exec", "qwen-mirror-test-backend-1", "bash", "-c",
                    f"DOCKER_HOST={docker_host} docker run --rm --env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin {config['image']} bash -c '{setup_script} && /usr/bin/yum --disablerepo=\"*\" --enablerepo=\"{repo_name}\" list available {package} 2>/dev/null | grep -E \"^{package}\"'"
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and package in result.stdout:
                    print(f"  [OK] {package}: Available")
                else:
                    print(f"  [NO] {package}: Not found")

            except Exception as e:
                if "timeout" in str(e).lower():
                    print(f"  [TO] {package}: Timeout")
                else:
                    print(f"  [ER] {package}: Error - {str(e)[:50]}")

if __name__ == "__main__":
    test_package_availability()