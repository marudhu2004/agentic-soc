import requests
import json

# ==========================================
# CONFIGURATION
# ==========================================
API_URL = "https://localhost:55000"
USER = "wazuh-wui"              
PASS = "MyS3cr37P450r.*-"

# Clean way to disable SSL warnings without importing urllib3 explicitly
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def get_token():
    """Authenticates and returns a JWT Bearer Token."""
    auth_url = f"{API_URL}/security/user/authenticate"
    
    try:
        # Basic Auth is required to get the initial token
        response = requests.get(auth_url, auth=(USER, PASS), verify=False)
        response.raise_for_status() # Raises error for 401/403/500
        
        token = response.json()['data']['token']
        print("[+] Authentication Successful. Token acquired.")
        return token

    except requests.exceptions.RequestException as e:
        print(f"[-] Authentication Failed: {e}")
        if response.content:
             print(f"    Server replied: {response.text}")
        return None

def get_agents(token):
    """Fetches the list of active agents."""
    # We query '/agents' because it's the most reliable "Hello World" for the Manager API
    url = f"{API_URL}/agents?pretty=true"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        
        data = response.json()
        agents = data['data']['affected_items']
        
        print(f"[+] Found {data['data']['total_affected_items']} Agent(s):")
        for agent in agents:
            status_icon = "🟢" if agent['status'] == 'active' else "🔴"
            print(f"   {status_icon} ID: {agent['id']} | Name: {agent['name']} | IP: {agent.get('ip', '127.0.0.1')}")

    except requests.exceptions.RequestException as e:
        print(f"[-] Data Fetch Failed: {e}")

if __name__ == "__main__":
    jwt = get_token()
    if jwt:
        get_agents(jwt)