# Auto-Deploy on push to main

Sets up: push to `main` → GitHub Actions opens an SSH connection to the
production server → a forced command on the server pulls, runs the smoke
test, and restarts `gatekeeper.service` only if the test passes.

Workflow file: [`/.github/workflows/deploy.yml`](/.github/workflows/deploy.yml).
It does nothing but open an SSH connection — the actual deploy logic lives in
`deploy.sh` **on the server**, kept outside the git checkout on purpose (see
below).

## Why the deploy logic lives outside the repo

`deploy.sh` sits at `/opt/gatekeeper/deploy.sh`, not inside
`/opt/gatekeeper/app` (the git checkout). If it lived inside the checkout, a
bad push could modify or delete the very script that's supposed to gate
deploys. The SSH key used by GitHub Actions can *only* ever run this one
fixed script, via a forced `command=` in `authorized_keys` — even a leaked
private key can't run arbitrary commands on the server.

## Setup

### 1. Generate a dedicated deploy keypair (on your local machine)

```bash
ssh-keygen -t ed25519 -f ./gatekeeper-deploy -N "" -C "github-actions-deploy"
```

Produces `gatekeeper-deploy` (private) and `gatekeeper-deploy.pub` (public).

### 2. Add the public key on the server — with a forced command

As the service user that owns `/opt/gatekeeper/app`:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys <<'EOF'
command="/opt/gatekeeper/deploy.sh",no-agent-forwarding,no-port-forwarding,no-pty,no-X11-forwarding ssh-ed25519 AAAA... github-actions-deploy
EOF
chmod 600 ~/.ssh/authorized_keys
```

Replace `AAAA...` with the contents of `gatekeeper-deploy.pub`.

### 3. Place `deploy.sh` on the server

```bash
scp deploy.sh <service-user>@<server>:/opt/gatekeeper/deploy.sh
ssh <service-user>@<server> 'chmod 700 /opt/gatekeeper/deploy.sh'
```

```bash
#!/usr/bin/env bash
# Lives at /opt/gatekeeper/deploy.sh on the server -- deliberately OUTSIDE the
# git checkout (/opt/gatekeeper/app), so a bad push can never modify or delete
# the very script that's supposed to gate it.
#
# Invoked only via the forced SSH command in the deploy user's authorized_keys
# (see setup instructions) -- never runs with any other arguments/behaviour.
set -euo pipefail

APP_DIR=/opt/gatekeeper/app
VENV_PYTHON=/opt/gatekeeper/venv/bin/python3
SERVICE=gatekeeper.service

cd "$APP_DIR"

echo "== Fetching latest main =="
git fetch origin main
# --ff-only: refuses to move if the local checkout has diverged (e.g. someone
# hand-edited a tracked file directly on the server) instead of silently
# discarding it. Fails loudly here rather than papering over it.
git merge --ff-only origin/main

echo "== Running smoke test (tests/test_cog_imports.py) =="
if ! "$VENV_PYTHON" tests/test_cog_imports.py; then
    echo "!! Smoke test failed -- NOT restarting $SERVICE. The old process keeps running."
    exit 1
fi

echo "== Smoke test passed, restarting $SERVICE =="
sudo /usr/bin/systemctl restart "$SERVICE"
echo "== Deploy complete =="
```

### 4. Grant sudo for exactly the restart command, nothing else

On the server: `sudo visudo -f /etc/sudoers.d/gatekeeper-deploy`:

```
<service-user> ALL=(root) NOPASSWD: /usr/bin/systemctl restart gatekeeper.service
```

### 5. Collect the server's host key (for pinned `known_hosts`)

```bash
ssh-keyscan -t ed25519 <server-ip-or-hostname> > known_hosts_entry.txt
```

Using a pinned `known_hosts` (rather than `StrictHostKeyChecking=no`) avoids
trusting whatever host key happens to answer at connect time.

### 6. Add GitHub repo secrets

`Settings → Secrets and variables → Actions → New repository secret`:

| Secret | Value |
|---|---|
| `DEPLOY_SSH_KEY` | contents of `gatekeeper-deploy` (the private key, in full) |
| `DEPLOY_USER` | the service user on the server |
| `DEPLOY_HOST` | server IP or hostname |
| `DEPLOY_KNOWN_HOSTS` | contents of `known_hosts_entry.txt` from step 5 |

### 7. Test before going live

Run `deploy.sh` manually on the server first:

```bash
sudo -u <service-user> /opt/gatekeeper/deploy.sh
```

Once that succeeds, push `deploy.yml` to `main` and watch the Actions tab on
the next push.

## Safety properties

- `git merge --ff-only` aborts instead of silently discarding any local
  changes made directly on the server (e.g. a one-off diagnostic script, see
  `DEPLOYMENT_LOG.md`).
- The bot is restarted **only if** `tests/test_cog_imports.py` passes — a
  broken push leaves the old, working process running untouched instead of
  replacing it with something broken.
- The forced SSH command means a leaked `DEPLOY_SSH_KEY` secret can only ever
  trigger this one script — never an arbitrary command on the server.
