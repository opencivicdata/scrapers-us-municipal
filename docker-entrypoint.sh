#!/bin/sh
set -e

pupa dbinit us

exec "$@"
