#!/bin/bash

# Your custom commands
chown www-data:www-data ./p

# Delegate to the original entrypoint script.
exec ./Docker/entrypoint.sh "$@"
