#!/bin/bash

# Your custom commands
chmod www-data:www-data ./p

# Delegate to the original entrypoint script.
exec ./Docker/entrypoint.sh "$@"
