#!/bin/bash

set -e # Exit immediately if a command exits with a non-zero status.
set -u # Treat unset variables as an error.

chown -R $USER_ID:$GROUP_ID /app
chown -R $USER_ID:$GROUP_ID /etc/services.d/app/

# vim:ft=sh:ts=4:sw=4:et:sts=4