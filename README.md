# Trivy Dashboard
A local web-based dashboard for running [Trivy](https://github.com/aquasecurity/trivy) vulnerability scans against Docker images, running containers, filesystems, and Git repositories. Results are displayed in a clean UI with severity breakdowns, risk scoring, secret detection, misconfiguration analysis, and scan history.
---
## Features
- **Multiple scan targets** — Docker images, running containers, local filesystems, and Git repositories
- **Vulnerability breakdown** — counts by severity: Critical, High, Medium, Low, Unknown
- **Risk score** — composite score with description and fix-impact estimate
- **Fixable CVE tracking** — highlights vulnerabilities that have an available fix
- **Secrets detection** — finds hardcoded secrets and credentials
- **Misconfiguration detection** — identifies security misconfigurations
- **CVE age stats** — average and oldest CVE age in days
- **Charts** — severity bar chart and top affected packages
- **Export** — download results as CSV
- **Scan history** — stores the last 50 scans in a local SQLite database with delete support
- **Dark mode** — toggle between light and dark themes
- **Desktop launcher** — `.desktop` file for Linux application menus
---
## Prerequisites
| Requirement | Notes |
|-------------|-------|
| Python 3.8+ | For the FastAPI backend |
| [Trivy](https://aquasecurity.github.io/trivy/latest/getting-started/installation/) | Must be on your `PATH` |
| Docker | Required only for image/container scans |
---
## Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/cjrs04/Trivy-dashboard.git
   cd Trivy-dashboard
   ```
2. **Create a Python virtual environment and install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn aiofiles
   ```
3. **Install Trivy** (if not already installed)
   ```bash
   sudo apt install trivy        # Debian/Ubuntu
   # or follow https://aquasecurity.github.io/trivy/latest/getting-started/installation/
   ```
---
## Usage
### Start the dashboard
```bash
./start.sh
```
The script will:
- Check that the virtual environment, `server.py`, and `trivy` are present
- Kill any existing process on port `8000`
- Start the FastAPI server in the background
- Open your browser at `http://localhost:8000`
- Stream server logs to the terminal
Press **Ctrl+C** to stop the server.
### Manual start (without the script)
```bash
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```
Then open `http://localhost:8000` in your browser.
---
## Desktop Launcher (Linux)
Copy the provided `.desktop` file to your applications directory and update the path if needed:
```bash
cp trivy-dashboard.desktop ~/.local/share/applications/
```
> **Note:** Edit the `Exec` path inside the file if you cloned to a location other than `~/trivy-dashboard`.
---
## Scan Types
| Type | Target example | Notes |
|------|---------------|-------|
| **Image** | `nginx:latest` | Scans a Docker image from a registry or local cache |
| **Container** | Running container | Select from a dropdown of active containers |
| **Filesystem** | `/path/to/dir` | Scans a local directory |
| **Git Repo** | `https://github.com/org/repo` | Scans a remote Git repository |
### Scanner options
Each scan can enable or disable individual scanners via checkboxes:
- **Vulnerabilities** (always on)
- **Secrets**
- **Misconfigurations**
- **Hide unfixed** — filters out CVEs with no available fix
---
## API Endpoints
The FastAPI backend exposes the following REST endpoints:
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/containers` | List running Docker containers |
| `GET` | `/scan` | Run a Trivy scan and save results |
| `GET` | `/history` | Retrieve the last 50 scan records |
| `DELETE` | `/history/{id}` | Delete a specific scan record |
**Scan query parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target` | string | required | The target to scan |
| `scan_type` | string | `image` | `image`, `container`, `fs`, or `repo` |
| `scanners` | string | `vuln` | Comma-separated list: `vuln`, `secret`, `misconfig` |
| `hide_unfixed` | bool | `false` | Exclude vulnerabilities without a fix |
---
## Data Storage
Scan results are stored in a SQLite database at `~/.trivy-dashboard.db`. Each record includes:
- Image/target name
- Scan timestamp and duration
- Vulnerability counts by severity
- Number of fixable CVEs
- Full raw JSON results from Trivy
---
## Project Structure
```
Trivy-dashboard/
├── server.py               # FastAPI backend
├── index.html              # Frontend UI
├── trivy-dashboard.css     # Stylesheet (light & dark themes)
├── start.sh                # Launch script
├── trivy-dashboard.desktop # Linux desktop launcher
└── venv/                   # Python virtual environment (created by user)
```
---
## License
This project is open source. See the repository for details.
