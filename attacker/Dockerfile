FROM kalilinux/kali-rolling

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# 1. Update & Install Tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    kali-defaults \
    iputils-ping \
    net-tools \
    curl \
    wget \
    nmap \
    sqlmap \
    hydra \
    gobuster \
    python3-requests \
    wordlists \
    gzip \
    bash-completion \
    && rm -rf /var/lib/apt/lists/*

# 2. Fix Wordlists (Unzip RockYou)
RUN if [ -f /usr/share/wordlists/rockyou.txt.gz ]; then \
      gzip -d /usr/share/wordlists/rockyou.txt.gz; \
    fi

# 3. Set Default Shell to BASH (Overrides Kali's ZSH default)
RUN chsh -s /bin/bash root

# 4. Keep container running
CMD ["tail", "-f", "/dev/null"]