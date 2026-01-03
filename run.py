import os
import subprocess
import sys
import argparse
import shlex
import pathlib
import time

# ==========================================
# CONFIGURATION
# ==========================================
WAZUH_SUBMODULE = "wazuh-setup"
CERT_REL_PATH = os.path.join("config", "wazuh_indexer_ssl_certs", "root-ca.pem")

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    RESET = '\033[0m'

def log(msg, color=Colors.BLUE):
    print(f"{color}[*] {msg}{Colors.RESET}")

def get_compose_base_cmd(root_dir):
    """Returns the base docker compose command with all context flags."""
    # Convert root_dir to string just in case, though subprocess handles Path objects usually
    root_str = str(root_dir)
    
    # We use the submodule as the project directory so official config paths resolve correctly.
    # We use relative paths for the files, anchored to the project directory logic.
    return [
        "docker", "compose",
        "--project-directory", os.path.join(root_str, WAZUH_SUBMODULE),
        "-f", os.path.join(root_str, WAZUH_SUBMODULE, "docker-compose.yml"), # Official Base
        "-f", os.path.join(root_str, "docker-compose.yml")                   # Your Root Override
    ]

def run_command(cmd, cwd=None, capture=False):
    """Runs a subprocess command."""
    try:
        # On Windows, shell=True helps with resolving paths in some environments
        use_shell = (os.name == 'nt')
        
        if capture:
            result = subprocess.run(cmd, cwd=cwd, shell=use_shell, capture_output=True, text=True)
            return result.returncode, result.stdout
        else:
            subprocess.run(cmd, cwd=cwd, check=True, shell=use_shell)
            return 0, ""
    except subprocess.CalledProcessError as e:
        if not capture:
            log(f"Command failed: {e}", Colors.FAIL)
            sys.exit(1)
        return e.returncode, e.stdout

def configure_wazuh(root_dir):
    """Waits for Manager daemons to be FULLY active before configuring."""
    log("Checking Wazuh Manager status...", Colors.BLUE)
    max_retries = 30
    
    for i in range(max_retries):
        base_cmd = get_compose_base_cmd(root_dir)
        check_cmd = base_cmd + ["exec", "wazuh.manager", "/var/ossec/bin/agent_groups", "-l"]
        
        # Capture output to check for application-level errors
        code, output = run_command(check_cmd, cwd=root_dir, capture=True)
        
        # STRICT CHECK: Ensure no internal errors are present in the output
        if code == 0 and "Error" not in output and "not ready" not in output:
            
            # 1. Check if group exists
            if "web-servers" in output:
                log("Configuration already exists (Group 'web-servers' found). Skipping setup.", Colors.GREEN)
                return 

            log("Manager services ready. Creating 'web-servers' group...", Colors.YELLOW)
            
            # 2. Create Group
            create_cmd = base_cmd + ["exec", "wazuh.manager", "/var/ossec/bin/agent_groups", "-a", "-g", "web-servers", "-q"]
            run_command(create_cmd, cwd=root_dir)
            
            # 3. Restart Agent
            log("Restarting Victim Agent to apply new configuration...", Colors.BLUE)
            restart_cmd = base_cmd + ["restart", "wazuh-sidecar"] 
            run_command(restart_cmd, cwd=root_dir)
            
            log("Configuration Complete.", Colors.GREEN)
            return
        
        # If we see "daemons not ready", we wait here
        if i % 2 == 0: print(".", end="", flush=True)
        time.sleep(5)

    log("\n[!] Manager service timeout. Run 'python run.py --setup' again in a minute.", Colors.FAIL)

def action_setup(root_dir):
    """Handles the Setup lifecycle: Certs -> Build -> Launch -> Configure."""
    abs_base_dir = os.path.join(root_dir, WAZUH_SUBMODULE)
    abs_cert_path = os.path.join(abs_base_dir, CERT_REL_PATH)

    log("PHASE 1: Certificate Check", Colors.BLUE)
    if os.path.exists(abs_cert_path):
        log("SSL Certificates found. Skipping generation.", Colors.GREEN)
    else:
        log("SSL Certificates missing. Generating now...", Colors.YELLOW)
        if not os.path.exists(abs_base_dir):
             log(f"Error: {WAZUH_SUBMODULE} submodule missing!", Colors.FAIL)
             sys.exit(1)
        
        # Generator must run from the submodule dir to find local configs
        gen_cmd = ["docker", "compose", "-f", "generate-indexer-certs.yml", "run", "--rm", "generator"]
        run_command(gen_cmd, cwd=abs_base_dir)

    log("PHASE 2: Launching Stack", Colors.BLUE)
    base_cmd = get_compose_base_cmd(root_dir)
    # We add --build to ensure your Attacker/Custom images are always fresh
    run_command(base_cmd + ["up", "-d", "--build"], cwd=root_dir)

    log("PHASE 3: Post-Launch Configuration", Colors.BLUE)
    configure_wazuh(root_dir)

    print(f"\n{Colors.GREEN}[SUCCESS] Lab is running!{Colors.RESET}")
    print(f" - SIEM:     https://localhost (admin / SecretPassword)")
    print(f" - Victim:   http://localhost:80")
    print(f" - Attacker: python run.py --probe \"attacker bash\"")

def action_probe(root_dir, probe_str):
    """Wraps 'docker compose exec' to run commands in the correct context."""
    parts = shlex.split(probe_str)
    if len(parts) < 2:
        log("Invalid probe format. Use: --probe \"service_name command\"", Colors.FAIL)
        sys.exit(1)
    
    service_name = parts[0]
    command_args = parts[1:]

    base_cmd = get_compose_base_cmd(root_dir)
    full_cmd = base_cmd + ["exec", service_name] + command_args
    
    log(f"Probing Service: {service_name}...", Colors.YELLOW)
    
    # We do NOT capture output here, so the user sees the interactive shell or output directly
    subprocess.run(full_cmd, cwd=root_dir, check=False)

def action_down(root_dir):
    """Tears down the stack correctly."""
    log("Stopping Lab...", Colors.YELLOW)
    base_cmd = get_compose_base_cmd(root_dir)
    run_command(base_cmd + ["down"], cwd=root_dir)
    log("Lab stopped.", Colors.GREEN)

def action_nuke(root_dir):
    """Destructive teardown: Removes containers, networks, AND VOLUMES."""
    print(f"{Colors.FAIL}WARNING: This will wipe all data (Logs, Alerts, Agent Keys).{Colors.RESET}")
    confirm = input("Are you sure? (y/N): ")
    
    if confirm.lower() == 'y':
        log("Nuking the environment...", Colors.YELLOW)
        base_cmd = get_compose_base_cmd(root_dir)
        # -v is the flag that deletes named volumes
        run_command(base_cmd + ["down", "-v"], cwd=root_dir)
        log("Environment is clean. All data destroyed.", Colors.GREEN)
    else:
        log("Nuke aborted.", Colors.BLUE)

def main():
    # Robustly find the directory where this script lives
    root_dir = pathlib.Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="Agentic SOC Lab Wrapper")
    parser.add_argument("--setup", action="store_true", help="Generate certs, build, and launch the lab")
    parser.add_argument("--down", action="store_true", help="Stop the lab (keep data)")
    parser.add_argument("--nuke", action="store_true", help="Stop the lab AND delete all data (Logs, Keys)")
    parser.add_argument("--probe", type=str, help="Run a command: --probe \"service command\"")
    
    args = parser.parse_args()

    print(f"{Colors.GREEN}=========================================={Colors.RESET}")
    print(f"{Colors.GREEN}   AGENTIC SOC LAB - CLI MANAGER          {Colors.RESET}")
    print(f"{Colors.GREEN}=========================================={Colors.RESET}")

    if args.setup:
        action_setup(root_dir)
    elif args.down:
        action_down(root_dir)
    elif args.nuke:
        action_nuke(root_dir)
    elif args.probe:
        action_probe(root_dir, args.probe)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
