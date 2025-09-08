#!/bin/bash
set -e
echo "Running Postman collections with Newman (local)"
for coll in postman/*.postman_collection.json; do
  echo "=== Running $coll ==="
  newman run "$coll" -e postman/environment.medisupply.local.json --insecure
done
