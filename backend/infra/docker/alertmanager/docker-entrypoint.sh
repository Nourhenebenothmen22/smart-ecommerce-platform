#!/bin/sh
set -e

CONFIG_SRC=/etc/alertmanager/alertmanager.yml
CONFIG_TMP=/tmp/alertmanager.yml

cp "$CONFIG_SRC" "$CONFIG_TMP"

for var in $(grep -oE '\$\{[A-Z_]+' "$CONFIG_TMP" | sed 's/\${//' | sort -u); do
    eval "value=\"\${$var}\""
    esc_value=$(echo "$value" | sed 's/[\/&]/\\&/g')
    sed -i "s/\${$var:-[^}]*}/$esc_value/g" "$CONFIG_TMP"
    sed -i "s/\${$var}/$esc_value/g" "$CONFIG_TMP"
done

exec /bin/alertmanager "$@"
