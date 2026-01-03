#!/bin/bash

# Register the agent with the manager using the environment variable
if [ -n "$WAZUH_MANAGER" ]; then
  echo "Registering with Wazuh Manager: $WAZUH_MANAGER"
  sed -i "s/MANAGER_IP/$WAZUH_MANAGER/g" /var/ossec/etc/ossec.conf
fi

# Start the agent in the background
/var/ossec/bin/wazuh-control start

# Keep the container alive by tailing the logs
echo "Wazuh Agent started. Tailing logs..."
tail -f /var/ossec/logs/ossec.log