# Start from the official Nginx Alpine image
FROM nginx:alpine

# The base image symlinks access.log to stdout.
# We remove this link so that Nginx writes to a real file, which
# can then be read by the Wazuh agent sidecar from the shared volume.
RUN rm /var/log/nginx/access.log
