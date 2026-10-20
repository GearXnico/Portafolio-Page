#!/usr/bin/env bash
# Deploys one version of the site on the server: deploy/deploy.sh <image tag>
# Task 5.3. deploy.yml runs it over SSH with the commit SHA as the tag; you can also run it by hand.
#
# 1. Pulls the API and web images of that tag from GHCR (GitHub Container Registry).
# 2. Backs up the database before migrating.
# 3. Runs the migrations and swaps the containers, waiting for their health checks.
# 4. If anything fails, starts the previous version again and exits with an error.
#
# The previous version can always come back because migrations only add (ADR 0007), so the
# old code still works on the migrated database and no restore is needed.
set -euo pipefail
umask 077

tag="${1:-}"
if [[ ! "$tag" =~ ^[A-Za-z0-9_.-]{1,128}$ ]]; then
  echo "usage: deploy.sh <image tag>, for example the 40-character commit SHA" >&2
  exit 2
fi

cd "$(dirname "$0")"
compose=(docker compose -f compose.prod.yml --env-file .env)
previous="$(cat .deployed-tag 2>/dev/null || true)"

# up: only images that already exist, never a build on the server (1 GB of memory).
start() {
  IMAGE_TAG="$1" "${compose[@]}" up -d --no-build --wait --wait-timeout 180 caddy
}

# DEPLOY_PULL=0 skips the pull, for CI, where the images were just built on the runner.
if [[ "${DEPLOY_PULL:-1}" != 0 ]]; then
  IMAGE_TAG="$tag" "${compose[@]}" pull --quiet migrate api caddy
fi

"${compose[@]}" up -d --wait db
mkdir -p backups
# shellcheck disable=SC2016 # the variables expand inside the db container, on purpose.
"${compose[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  > "backups/pre-deploy-$tag.dump"

if start "$tag"; then
  echo "$tag" > .deployed-tag
  # Keeps the last 5 pre-deploy backups; the daily ones are backup.sh's job.
  # shellcheck disable=SC2012 # the names are made by this script, without spaces.
  ls -1t backups/pre-deploy-*.dump | tail -n +6 | xargs -r rm --
  echo "Deployed $tag"
  exit 0
fi

echo "Deploy of $tag failed" >&2
"${compose[@]}" logs --no-color --tail 50 migrate api caddy >&2 || true
if [[ -z "$previous" ]]; then
  echo "There is no previous version to go back to: the site is down until a deploy works" >&2
elif start "$previous"; then
  echo "Rolled back to $previous" >&2
else
  echo "The rollback to $previous failed too: the site is down" >&2
fi
exit 1
