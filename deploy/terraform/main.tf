terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

# Look up existing SSH key by name
data "digitalocean_ssh_key" "default" {
  name = var.ssh_key_name
}

resource "digitalocean_droplet" "kelp" {
  name     = "kelp"
  region   = var.region
  size     = "s-1vcpu-512mb-10gb"
  image    = "ubuntu-24-04-x64"
  ssh_keys = [data.digitalocean_ssh_key.default.id]

  tags = ["kelp", "web"]
}

# DNS record for kelp.vroblock.io
data "digitalocean_domain" "vroblock" {
  name = var.domain
}

resource "digitalocean_record" "kelp" {
  domain = data.digitalocean_domain.vroblock.id
  type   = "A"
  name   = "kelp"
  value  = digitalocean_droplet.kelp.ipv4_address
  ttl    = 300
}

resource "digitalocean_firewall" "kelp" {
  name        = "kelp-fw"
  droplet_ids = [digitalocean_droplet.kelp.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# Generate Ansible inventory
resource "local_file" "ansible_inventory" {
  content = <<-EOF
    [kelp]
    ${digitalocean_droplet.kelp.ipv4_address} ansible_user=root ansible_ssh_private_key_file=${var.ssh_private_key_path}
  EOF
  filename = "${path.module}/../ansible/inventory.ini"
}
