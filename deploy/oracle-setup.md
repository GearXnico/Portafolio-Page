# Oracle server setup (task 5.2, free phase)

How to prepare the Oracle Always Free VM (virtual machine) from ADR (architecture decision record) 0010, production only. You do every step by hand once; after that, deploys are the `deploy` workflow (see `README.md` in this folder). If Oracle reclaims the VM, repeat steps 2 to 5 and 8, run the workflow and restore the latest backup.

Secrets are created only on the server and in GitHub. None of them goes into the repo, which is public.

## 1. Account and keys (your machine)

1. Create the Oracle Cloud account. Pick **Chile Central (Santiago)** as the home region: Always Free VMs only run in the home region, and it can't be changed later. It asks for a phone and a card, which is not charged unless you upgrade the account.
2. Create three keys on your machine:

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/oracle_admin -C oracle-admin       # you, as the ubuntu user
   ssh-keygen -t ed25519 -f ~/.ssh/portafolio_actions -N "" -C github-actions   # only for the deploy workflow
   age-keygen -o backup-key.txt                                      # backups; prints the public key (age1...)
   ```

   Save `backup-key.txt` in your password manager and in a second place, then delete the file. Without it no backup can be read.

## 2. VM and network (Oracle console)

1. **Compute > Instances > Create instance:** image Canonical Ubuntu 24.04, shape `VM.Standard.E2.1.Micro` (Always Free-eligible), a public IPv4 address, and the public key `~/.ssh/oracle_admin.pub`. If it says there is no capacity, try again later or another availability domain; if it keeps failing, ADR 0010 falls back to DigitalOcean, not Render.
2. **Networking > Virtual cloud networks > your VCN > Security Lists > Default:** add ingress rules from `0.0.0.0/0` for TCP 80, TCP 443 and UDP 443 (HTTP/3). Port 22 is already there.
3. Copy the instance OCID (Oracle Cloud ID) from its page; step 6 uses it.

## 3. Firewall and system (SSH as `ubuntu`)

Oracle's Ubuntu images ship their own iptables rules that reject everything except SSH, and Oracle advises against `ufw` on them ([Oracle's guide](https://blogs.oracle.com/developers/post/enabling-network-traffic-to-ubuntu-images-in-oracle-cloud-infrastructure)). Add the web ports right after the SSH rule, before the final REJECT:

```bash
ssh -i ~/.ssh/oracle_admin ubuntu@<ip>
sudo sed -i '/--dport 22 -j ACCEPT/a -A INPUT -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT\n-A INPUT -p tcp -m state --state NEW -m tcp --dport 443 -j ACCEPT\n-A INPUT -p udp -m udp --dport 443 -j ACCEPT' /etc/iptables/rules.v4
sudo iptables-restore < /etc/iptables/rules.v4
```

If you reload these rules after Docker is installed, run `sudo systemctl restart docker` so it adds its own rules again.

System updates, swap (1 GB of memory is tight while images are pulled) and the tools the scripts use:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades age pipx
sudo dpkg-reconfigure -plow unattended-upgrades          # answer Yes: automatic security updates
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Docker Engine and the Compose plugin from Docker's repository ([official steps](https://docs.docker.com/engine/install/ubuntu/)):

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

## 4. The `deploy` user

It runs the containers, the deploys and the backups. Being in the `docker` group makes it as powerful as root on this VM, so its key is only the workflow's, and `restrict` turns off port forwarding and terminals for it.

```bash
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG docker deploy
sudo install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
echo "restrict <content of ~/.ssh/portafolio_actions.pub from your machine>" | sudo tee /home/deploy/.ssh/authorized_keys
sudo chown deploy:deploy /home/deploy/.ssh/authorized_keys && sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo -iu deploy pipx install oci-cli==3.95.0              # uploads the backups (step 6)
```

## 5. `deploy/.env` on the server

```bash
sudo -iu deploy
mkdir -p ~/portafolio/deploy && cd ~/portafolio/deploy
nano .env && chmod 600 .env
```

Use `.env.example` as the list of variables, with **new** values (never the ones from your machine):

| Variable | Value |
|---|---|
| `POSTGRES_PASSWORD`, `APP_DB_PASSWORD` | `openssl rand -hex 24`, one each |
| `JWT_SECRET` | `openssl rand -hex 48` |
| `ADMIN_EMAIL` | your admin login |
| `ADMIN_PASSWORD_HASH` | fill it after step 8, once the images are public: `docker run --rm -it ghcr.io/gearxnico/portafolio-page/api:<sha> python -m app.hash_password`, pasted in single quotes |
| `SMTP_USER`, `SMTP_PASSWORD`, `CONTACT_NOTIFY_TO` | Gmail and its app password (ADR 0005); `SMTP_HOST=smtp.gmail.com` |
| `SITE_ADDRESS` | the domain from step 7, without `https://` |
| `IMAGE_PREFIX` | `ghcr.io/gearxnico/portafolio-page` |
| `BACKUP_AGE_RECIPIENT` | the `age1...` public key from step 1 |
| `BACKUP_BUCKET` | `portafolio-backups` |

Leave out the local-only ones (`DATABASE_URL`, `MIGRATION_DATABASE_URL`, the ports and `TRUSTED_PROXIES`, which the compose sets).

## 6. Backup bucket (Oracle console)

1. **Storage > Buckets > Create bucket** `portafolio-backups`, Standard tier, private (the default).
2. In the bucket, **Lifecycle policy rules > Create rule:** delete objects older than 14 days.
3. **Identity > Dynamic groups > Create** `portafolio-vm` with the rule `instance.id = '<instance OCID>'`.
4. **Identity > Policies > Create** in the root compartment (or the one with the bucket):

   ```
   Allow dynamic-group portafolio-vm to manage objects in tenancy where all {target.bucket.name='portafolio-backups', any {request.permission='OBJECT_CREATE', request.permission='OBJECT_INSPECT'}}
   Allow service objectstorage-sa-santiago-1 to manage object-family in tenancy
   ```

   The first one lets the VM create objects and list their names, but not read, overwrite or delete them ([Oracle's example](https://blogs.oracle.com/cloud-infrastructure/post/configuring-oci-object-storage-access-control-policies)). The second one lets the lifecycle rule delete old backups. If your tenancy uses identity domains and the name isn't found, write the group as `'Default'/'portafolio-vm'`.

## 7. Domain

Point an A record at the VM's public IP: a free DuckDNS subdomain, or the `.cl` domain at NIC Chile (CLP 9,990 a year). Caddy gets the HTTPS certificate on its own once the name resolves.

## 8. GitHub

1. **Settings > Environments > New environment** `production`, with **Deployment branches** limited to `main`, and these secrets:

   | Secret | Value |
   |---|---|
   | `DEPLOY_SSH_KEY` | the content of `~/.ssh/portafolio_actions` (private) |
   | `DEPLOY_KNOWN_HOSTS` | the output of `ssh-keyscan -t ed25519 <ip>`; check its fingerprint against `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the VM |
   | `DEPLOY_HOST` | the VM's public IP |
   | `DEPLOY_USER` | `deploy` |

2. After the first push to `main` publishes the images: **Packages > api** and **web > Package settings > Change visibility > Public**, so the server pulls them without a token.

## 9. First deploy and backups

1. **Actions > deploy > Run workflow** with the full SHA of `main`. It ends green when `/api/health` answers.
2. Daily backup, as `deploy` (`crontab -e`):

   ```
   PATH=/home/deploy/.local/bin:/usr/local/bin:/usr/bin:/bin
   15 4 * * * $HOME/portafolio/deploy/backup.sh >> $HOME/backup.log 2>&1
   ```

3. Run `~/portafolio/deploy/backup.sh` once by hand and check that the file shows up in the bucket.
4. Restore test (plan task 5.4): download that file and follow "Backups and restore" in `README.md` on your machine.
