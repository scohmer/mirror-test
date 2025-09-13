#!/bin/bash

# Linux Mirror Testing Solution - Repository Test Script
# This script tests if a repository is functional for a given distribution

set -e  # Exit on any error

# Default values
DISTRIBUTION="ubuntu"
VERSION="20.04"
REPO_URL="http://archive.ubuntu.com/ubuntu"
TEST_TYPE="update"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --distribution)
            DISTRIBUTION="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --repo-url)
            REPO_URL="$2"
            shift 2
            ;;
        --test-type)
            TEST_TYPE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check repository connectivity
check_connectivity() {
    local url="$1"
    log "Checking connectivity to $url..."
    
    if command -v curl >/dev/null 2>&1; then
        if curl --connect-timeout 10 --max-time 30 -f -s "$url" >/dev/null; then
            log "✓ Successfully connected to repository"
            return 0
        else
            log "✗ Failed to connect to repository"
            return 1
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget --timeout=30 --tries=1 -q -O /dev/null "$url" 2>/dev/null; then
            log "✓ Successfully connected to repository"
            return 0
        else
            log "✗ Failed to connect to repository"
            return 1
        fi
    else
        log "⚠ Neither curl nor wget found, skipping connectivity check"
        return 0
    fi
}

# Function to test repository update
test_update() {
    log "Testing repository update for $DISTRIBUTION $VERSION..."
    
    # Create a temporary directory for testing
    local temp_dir=$(mktemp -d)
    local result_file="$temp_dir/result"
    
    # Try to run apt-get update with our repository
    if [ "$DISTRIBUTION" = "debian" ] || [ "$DISTRIBUTION" = "ubuntu" ]; then
        # For Debian/Ubuntu based systems
        if command -v apt-get >/dev/null 2>&1; then
            log "Running apt-get update with custom repository..."
            
            # Create a temporary sources list
            local sources_list="$temp_dir/sources.list"
            echo "deb $REPO_URL $VERSION main" > "$sources_list"
            echo "deb-src $REPO_URL $VERSION main" >> "$sources_list"
            
            # Run apt-get update with our custom sources
            if apt-get -o Dir::Etc::sourcelist="$sources_list" -o Dir::Etc::sourceparts="" -o APT::Get::List-Cleanup="0" update >"$result_file" 2>&1; then
                log "✓ Repository update successful"
                return 0
            else
                log "✗ Repository update failed"
                cat "$result_file"
                return 1
            fi
        else
            log "⚠ apt-get not found, skipping update test"
            return 0
        fi
    elif [ "$DISTRIBUTION" = "rocky" ] || [ "$DISTRIBUTION" = "rhel" ]; then
        # For RHEL/centos based systems
        if command -v dnf >/dev/null 2>&1; then
            log "Running dnf repolist with custom repository..."
            
            # Create a temporary repo file
            local repo_file="$temp_dir/test.repo"
            cat > "$repo_file" << EOF
[test-repo]
name=Test Repository
baseurl=$REPO_URL
enabled=1
gpgcheck=0
EOF
            
            if dnf --disablerepo='*' --enablerepo='test-repo' repolist >"$result_file" 2>&1; then
                log "✓ Repository repolist successful"
                return 0
            else
                log "✗ Repository repolist failed"
                cat "$result_file"
                return 1
            fi
        elif command -v yum >/dev/null 2>&1; then
            log "Running yum repolist with custom repository..."
            
            # Create a temporary repo file
            local repo_file="$temp_dir/test.repo"
            cat > "$repo_file" << EOF
[test-repo]
name=Test Repository
baseurl=$REPO_URL
enabled=1
gpgcheck=0
EOF
            
            if yum --disablerepo='*' --enablerepo='test-repo' repolist >"$result_file" 2>&1; then
                log "✓ Repository repolist successful"
                return 0
            else
                log "✗ Repository repolist failed"
                cat "$result_file"
                return 1
            fi
        else
            log "⚠ Neither dnf nor yum found, skipping repolist test"
            return 0
        fi
    else
        log "⚠ Unknown distribution $DISTRIBUTION, skipping repository test"
        return 0
    fi
}

# Function to test package installation
test_installation() {
    log "Testing package installation for $DISTRIBUTION $VERSION..."
    
    if [ "$DISTRIBUTION" = "debian" ] || [ "$DISTRIBUTION" = "ubuntu" ]; then
        # For Debian/Ubuntu based systems
        if command -v apt-get >/dev/null 2>&1; then
            local package="curl"
            log "Installing test package: $package"
            
            if apt-get install -y --no-install-recommends "$package" > /dev/null 2>&1; then
                log "✓ Package installation successful"
                return 0
            else
                log "✗ Package installation failed"
                return 1
            fi
        else
            log "⚠ apt-get not found, skipping package installation test"
            return 0
        fi
    elif [ "$DISTRIBUTION" = "rocky" ] || [ "$DISTRIBUTION" = "rhel" ]; then
        # For RHEL/centos based systems
        if command -v dnf >/dev/null 2>&1; then
            local package="curl"
            log "Installing test package: $package"
            
            if dnf install -y "$package" > /dev/null 2>&1; then
                log "✓ Package installation successful"
                return 0
            else
                log "✗ Package installation failed"
                return 1
            fi
        elif command -v yum >/dev/null 2>&1; then
            local package="curl"
            log "Installing test package: $package"
            
            if yum install -y "$package" > /dev/null 2>&1; then
                log "✓ Package installation successful"
                return 0
            else
                log "✗ Package installation failed"
                return 1
            fi
        else
            log "⚠ Neither dnf nor yum found, skipping package installation test"
            return 0
        fi
    else
        log "⚠ Unknown distribution $DISTRIBUTION, skipping package installation test"
        return 0
    fi
}

# Main execution flow
main() {
    log "Starting repository test for $DISTRIBUTION $VERSION with URL: $REPO_URL"
    
    # Check connectivity first
    if ! check_connectivity "$REPO_URL"; then
        log "Repository connectivity test failed"
        exit 1
    fi
    
    # Run the appropriate tests based on test type
    case "$TEST_TYPE" in
        update)
            if test_update; then
                log "Repository update test passed"
                exit 0
            else
                log "Repository update test failed"
                exit 1
            fi
            ;;
        install)
            if test_installation; then
                log "Package installation test passed"
                exit 0
            else
                log "Package installation test failed"
                exit 1
            fi
            ;;
        repolist)
            if test_update; then
                log "Repository repolist test passed"
                exit 0
            else
                log "Repository repolist test failed"
                exit 1
            fi
            ;;
        all)
            # Run all tests in sequence
            if check_connectivity "$REPO_URL" && test_update && test_installation; then
                log "All repository tests passed"
                exit 0
            else
                log "Some repository tests failed"
                exit 1
            fi
            ;;
        *)
            log "Unknown test type: $TEST_TYPE"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
