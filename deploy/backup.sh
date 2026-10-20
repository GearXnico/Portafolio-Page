#!/usr/bin/env bash
# Daily backup of the database and /media, encrypted and sent off the server. Task 5.4, ADR (architecture decision record) 0010.
# cron runs it on the server as the deploy user (deploy/README.md):
#   15 4 * * * ~/portafolio/deploy/backup.sh >> ~/backup.log 2>&1
#
# 1. pg_dump of the database and a tar of /media, both read from the running containers.
# 2. Encrypts them with age to BACKUP_AGE_RECIPIENT, a public key: the private key is only with
#    Nicolas, so neither the server nor the bucket can read a backup.
# 3. Uploads the file to the private Object Storage bucket BACKUP_BUCKET with the VM's own identity
#    (instance principal): there is no key on the server, and the policy only lets it create objects
#    and list their names, not read, overwrite or delete them. The bucket deletes them after 14 days.
# Restoring is in deploy/README.md.
set -euo pipefail
umask 077

cd "$(dirname "$0")"
compose=(docker compose -f compose.prod.yml --env-file .env)

# Reads one variable from .env without running it as shell code.
env_value() { sed -n "s/^$1=//p" .env | tail -n 1; }
recipient="$(env_value BACKUP_AGE_RECIPIENT)"
bucket="$(env_value BACKUP_BUCKET)"
if [[ ! "$recipient" =~ ^age1[0-9a-z]{58}$ ]]; then
  echo "BACKUP_AGE_RECIPIENT in deploy/.env must be an age public key (age1...)" >&2
  exit 1
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# shellcheck disable=SC2016 # the variables expand inside the db container, on purpose.
"${compose[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  > "$work/db.dump"
"${compose[@]}" exec -T api tar -C /media -cf - . > "$work/media.tar"

mkdir -p backups
name="portafolio-$(date -u +%Y%m%dT%H%M%SZ).tar.age"
tar -C "$work" -cf - db.dump media.tar | age --encrypt --recipient "$recipient" > "backups/$name"
echo "Backup encrypted: backups/$name ($(du -h "backups/$name" | cut -f1))"

# The server keeps the last 3, for a quick restore without downloading.
# shellcheck disable=SC2012 # the names are made by this script, without spaces.
ls -1t backups/portafolio-*.tar.age | tail -n +4 | xargs -r rm --

if [[ -z "$bucket" ]]; then
  echo "BACKUP_BUCKET is empty: this backup stays only on this server" >&2
  exit 0
fi
oci os object put --auth instance_principal --bucket-name "$bucket" \
  --file "backups/$name" --name "$name"
echo "Uploaded to the bucket $bucket"
