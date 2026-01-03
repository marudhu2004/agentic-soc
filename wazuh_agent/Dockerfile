FROM ubuntu:22.04

# 1. Install prerequisites
RUN apt-get update && apt-get install -y curl gnupg apt-transport-https lsb-release

# 2. Add Wazuh repository
RUN curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | apt-key add -
RUN echo "deb https://packages.wazuh.com/4.x/apt/ stable main" | tee /etc/apt/sources.list.d/wazuh.list

# 3. Install Wazuh Agent
RUN apt-get update && apt-get install -y wazuh-agent=4.9.0-1

# 4. Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]