#!/usr/bin/env bash
set -euo pipefail

# hi_uploader.sh
# Usage: hi_uploader.sh [prop-file] [prop-key]
# Reads sonar-project.properties (default ./sonar-project.properties), finds sonar.projectKey and hi.file.path (or prop-key),
# and posts the file contents to SonarQube project settings key hi_plugin.content using curl and HTTP Basic auth (token:).

PROP_FILE=${1:-sonar-project.properties}
PROP_KEY=${2:-hi.file.path}
HOST=${SONAR_HOST_URL:-}
TOKEN=${SONAR_AUTH_TOKEN:-${SONAR_TOKEN:-}}

if [ ! -f "$PROP_FILE" ]; then
  echo "Error: properties file not found: $PROP_FILE" >&2
  exit 2
fi

# helper to extract property value (first match, trim spaces)
prop() {
  local key="$1" file="$2"
  grep -E "^${key}=" "$file" | head -n1 | cut -d'=' -f2- | sed -e 's/^\s*//' -e 's/\s*$//'
}

if [ -z "$HOST" ]; then
  HOST=$(prop 'sonar.host.url' "$PROP_FILE")
fi
PROJECT_KEY=$(prop 'sonar.projectKey' "$PROP_FILE")
FILE_PATH=$(prop "$PROP_KEY" "$PROP_FILE")

if [ -z "$HOST" ]; then
  echo "Error: Sonar host not set (set SONAR_HOST_URL or sonar.host.url in $PROP_FILE)" >&2
  exit 2
fi
if [ -z "$PROJECT_KEY" ]; then
  echo "Error: sonar.projectKey not found in $PROP_FILE" >&2
  exit 2
fi
if [ -z "$FILE_PATH" ]; then
  echo "Error: property '$PROP_KEY' not found in $PROP_FILE" >&2
  exit 2
fi

# resolve relative path
case "$FILE_PATH" in
  /*|~/*|[A-Za-z]:\\*)
    RESOLVED="$FILE_PATH"
    ;;
  *)
    RESOLVED="$(pwd)/$FILE_PATH"
    ;;
esac

if [ ! -f "$RESOLVED" ]; then
  echo "Error: file not found: $RESOLVED" >&2
  exit 2
fi

if [ -z "$TOKEN" ]; then
  echo "Error: SONAR_AUTH_TOKEN or SONAR_TOKEN not set (withSonarQubeEnv provides SONAR_AUTH_TOKEN)" >&2
  exit 2
fi

API_URL="${HOST%/}/api/settings/set"

curl -Ssf -u "$TOKEN:" "$API_URL" \
  --data-urlencode "component=$PROJECT_KEY" \
  --data-urlencode "key=hi_plugin.content" \
  --data-urlencode "value@${RESOLVED}"

echo "Upload succeeded"
