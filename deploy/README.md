# KELP Deployment

Deploy KELP to Digital Ocean with Terraform + Ansible. Includes automatic HTTPS via Caddy.

## Prerequisites

- [Terraform](https://terraform.io)
- [Ansible](https://ansible.com)
- Digital Ocean account with API token
- SSH key registered in DO

## Setup

1. Create `terraform/terraform.tfvars`:
   ```hcl
   do_token     = "dop_v1_xxxxx"
   ssh_key_name = "your-do-ssh-key-name"
   ```

2. Add your SSH key to the agent:
   ```bash
   ssh-add ~/.ssh/id_ed25519
   ```

3. Deploy:
   ```bash
   ./deploy.sh
   ```

4. Visit: **https://kelp.vroblok.io**

## Commands

| Action | Command |
|--------|---------|
| Full deploy | `./deploy.sh` |
| Redeploy code | `cd ansible && ansible-playbook -i inventory.ini playbook.yml` |
| Teardown | `cd terraform && terraform destroy` |
| SSH in | `ssh root@$(cd terraform && terraform output -raw droplet_ip)` |
| View logs | `ssh root@<IP> docker logs kelp` |
| Restart app | `ssh root@<IP> docker restart kelp` |

## Architecture

```
┌─────────────────────────────────────────┐
│  Digital Ocean Droplet                  │
│  s-1vcpu-512mb-10gb ($4/mo)            │
│  Ubuntu 24.04 LTS                       │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Caddy (reverse proxy + SSL)    │   │
│  │  :443 → localhost:8000          │   │
│  └─────────────────────────────────┘   │
│                 │                       │
│  ┌─────────────────────────────────┐   │
│  │  Docker: kelp container         │   │
│  │  Python 3.12 + uvicorn          │   │
│  │  Port 8000                      │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
         │
    DNS: kelp.vroblok.io
    Firewall: 22 (SSH), 80, 443 (HTTPS)
```

## Files

```
deploy/
├── deploy.sh              # One-command deploy
├── Dockerfile             # App container
├── terraform/
│   ├── main.tf            # Droplet, firewall, DNS
│   ├── variables.tf       # Input variables
│   ├── outputs.tf         # IP and URL outputs
│   └── terraform.tfvars   # (gitignored) Secrets
└── ansible/
    ├── playbook.yml       # Docker + Caddy setup
    └── inventory.ini      # (generated) Host list
```
