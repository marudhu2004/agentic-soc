import os
import subprocess
import sys
import time
import pathlib

# ==========================================
# CONFIGURATION
# ==========================================
# Path to the official submodule/clone
WAZUH_BASE_DIR = os.path.join("wazuh-setup")


# Path where certs are generated (relative to WAZUH_BASE_DIR)
CERT_CHECK_PATH = os.path.join("config", "wazuh_indexer_ssl_certs", "root-ca.pem")

# Docker Compose Files
BASE_COMPOSE = os.path.join(WAZUH_BASE_DIR, "docker-compose.yml")
OVERRIDE_COMPOSE = "docker-compose.yml"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    RESET = '\033[0m'

def log(msg, color=Colors.BLUE):
    print(f"{color}[*] {msg}{Colors.RESET}")

def run_command(cmd, cwd=None, shell=False):
    """Runs a command and exits if it fails."""
    try:
        # On Windows, shell=True is often needed for complex docker commands
        is_windows = os.name == 'nt'
        use_shell = shell or is_windows
        
        subprocess.run(cmd, cwd=cwd, check=True, shell=use_shell)
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {e}", Colors.FAIL)
        sys.exit(1)

def main():
    root_dir = os.getcwd()
    abs_base_dir = os.path.join(root_dir, WAZUH_BASE_DIR)
    print(WAZUH_BASE_DIR, abs_base_dir)
    abs_cert_path = os.path.join(abs_base_dir, CERT_CHECK_PATH)

    print(f"{Colors.GREEN}=========================================={Colors.RESET}")
    print(f"{Colors.GREEN}   AGENTIC SOC LAB - AUTOMATED LAUNCHER   {Colors.RESET}")
    print(f"{Colors.GREEN}=========================================={Colors.RESET}")

    # 1. Check if upstream repo exists
    if not os.path.exists(abs_base_dir):
        log("Wazuh-Docker submodule not found!", Colors.FAIL)
        log(f"Please run: git clone https://github.com/wazuh/wazuh-docker.git {os.path.join('wazuh-docker')}", Colors.YELLOW)
        sys.exit(1)

    # 2. Check for Certificates
    if os.path.exists(abs_cert_path):
        log("SSL Certificates found. Skipping generation.", Colors.GREEN)
    else:
        log("SSL Certificates missing. Generating now...", Colors.YELLOW)
        
        # We must run this FROM the single-node directory so it finds the ./config folder
        gen_cmd = ["docker", "compose", "-f", "generate-indexer-certs.yml", "run", "--rm", "generator"]
        run_command(gen_cmd, cwd=abs_base_dir)
        
        log("Certificates generated successfully.", Colors.GREEN)

    # 3. Launch the Stack
    log("Launching the Multi-Layer Environment...", Colors.BLUE)
    
    # We run this from the ROOT directory so it picks up the override file correctly
    launch_cmd = [
        "docker", "compose",
        "-f", BASE_COMPOSE,        # The Official Base
        "-f", OVERRIDE_COMPOSE,    # Your Layers & Victim
        "up", "-d"                 # Detached mode
    ]
    
    run_command(launch_cmd, cwd=root_dir)

    print(f"\n{Colors.GREEN}[SUCCESS] Lab is running!{Colors.RESET}")
    print(f" - SIEM:     https://localhost (admin / SecretPassword)")
    print(f" - Victim:   http://localhost:80")
    print(f" - Attacker: 'docker exec -it attacker bash'")
    print(f"\n{Colors.YELLOW}Note: Wait ~2-3 minutes for Wazuh Indexer to initialize.{Colors.RESET}")

if __name__ == "__main__":
    main()