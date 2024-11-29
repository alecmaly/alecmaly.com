#!/bin/bash

# Your custom commands
chmod user:user ./p

# Delegate to the original entrypoint script
exec ./Docker/entrypoint.sh "$@"
