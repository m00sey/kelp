terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

# Look up existing SSH key by name
data "hcloud_ssh_key" "default" {
  name = var.ssh_key_name
}

resource "hcloud_server" "kelp" {
  name        = "kelp"
  server_type = var.server_type
  image       = "ubuntu-24.04"
  location    = var.location
  ssh_keys    = [data.hcloud_ssh_key.default.id]

  labels = {
    app = "kelp"
    env = "web"
  }
}

resource "hcloud_firewall" "kelp" {
  name = "kelp-fw"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = var.ssh_allowed_cidrs
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction       = "out"
    protocol        = "tcp"
    port            = "1-65535"
    destination_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction       = "out"
    protocol        = "udp"
    port            = "1-65535"
    destination_ips = ["0.0.0.0/0", "::/0"]
  }
}

resource "hcloud_firewall_attachment" "kelp" {
  firewall_id = hcloud_firewall.kelp.id
  server_ids  = [hcloud_server.kelp.id]
}

# Generate Ansible inventory
resource "local_file" "ansible_inventory" {
  content = <<-EOF
    [kelp]
    ${hcloud_server.kelp.ipv4_address} ansible_user=root ansible_ssh_private_key_file=${var.ssh_private_key_path} ansible_ssh_common_args='-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=~/.ssh/known_hosts'
  EOF
  filename = "${path.module}/../ansible/inventory.ini"
}
