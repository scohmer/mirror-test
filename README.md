# Linux Mirror Testing Solution

An automated testing system for air-gapped Linux repository mirrors with a real-time web dashboard.

## Project Overview

This solution provides a containerized approach to testing Linux repository functionality across multiple distributions and versions. It offers both automated testing capabilities and a real-time web dashboard for monitoring test results.

## Supported Distributions

- **Debian**: 7, 8, 9, 10, 11, 12, 13
- **Ubuntu**: 18.04, 20.04, 22.04, 24.04, 25.04
- **Kali**: kali-rolling
- **Rocky Linux**: 8, 9, 10
- **RHEL**: 8, 9, 10

## Features

### Testing Capabilities
- Automated testing using containerized environments (Docker)
- Test repository package installation capabilities
- Verify repository connectivity and package availability
- Run tests in parallel for speed
- Package integrity validation

### Web Dashboard
- Real-time status updates with visual indicators:
  - Green (✓) = functional
  - Red (✗) = issues detected
- Display test progress and results
- Show last test timestamp and duration
- Manual test triggering capability

## Technical Architecture

### Backend
- **Framework**: FastAPI for REST API and WebSocket support
- **Containerization**: Docker for isolated testing environments
- **Task Management**: Asynchronous task execution
- **Database**: SQLite for storing test history and results
- **Real-time Updates**: WebSocket integration for live dashboard updates

### Frontend
- **Framework**: HTML/CSS/JavaScript with React/Vue.js components
- **Design**: Modern, responsive web UI
- **State Management**: Built-in JavaScript state management
- **Real-time Updates**: WebSocket integration for live status updates

### Testing Infrastructure
- **Base Images**: Official Docker images for each distribution
- **Test Scripts**: Bash scripts for repository validation
- **Health Checks**: 
  - `apt-get update` for Debian-based systems
  - `yum/dnf repolist` for RHEL-based systems
  - Package installation tests
  - Signature verification

## Deployment

### Prerequisites
- Docker and Docker Compose installed
- Air-gapped repository mirror configured

### Quick Start
1. Clone the repository
2. Configure your repository URLs in `config.yaml`
3. Run `docker-compose up --build`

### Configuration
Configuration is managed through:
- `config.yaml` - Centralized configuration file
- Environment variables for overrides

## Project Structure

```
.
├── backend/                # Python FastAPI backend
│   ├── main.py             # Main application entry point
│   ├── api/                # API endpoints
│   ├── core/               # Configuration and settings
│   ├── models/             # Data models
│   ├── services/           # Business logic
│   └── requirements.txt    # Python dependencies
├── frontend/               # Web dashboard
│   ├── index.html          # Main HTML file
│   ├── src/main.js         # JavaScript for WebSocket communication
│   └── styles/main.css     # CSS styling
├── test_scripts/           # Repository testing scripts
├── docker-compose.yml      # Docker Compose configuration
└── config.yaml             # Application configuration
```

## Getting Started

1. Configure your repository URLs in `config.yaml`
2. Build and start containers:
   ```bash
   docker-compose up --build
   ```
3. Access the dashboard at http://localhost:3000

## Development

### Backend Development
- Modify files in the `backend/` directory
- Rebuild the backend container to see changes:
  ```bash
  docker-compose build backend
  ```

### Frontend Development
- Modify files in the `frontend/` directory
- The frontend is served by the Nginx container, so changes are automatically reflected

## Testing Process

1. **Container Spin-up**: Creates minimal containers for each distribution/version
2. **Repository Configuration**: Points containers to air-gapped mirror
3. **Package Operations**: Tests package updates and installations
4. **Validation**: Checks package integrity and signature verification
5. **Reporting**: Returns success/failure status with detailed results

## Success Criteria

- All repositories can be tested within 5 minutes
- Dashboard updates in real-time (< 1 second delay)
- System handles concurrent tests without issues
- Clear visual feedback on repository health
- Historical data tracking for trend analysis

## Contributing

Contributions are welcome! Please submit a pull request with your changes.

## License

This project is licensed under the MIT License.
