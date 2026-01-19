output "droplet_ip" {
  value       = digitalocean_droplet.kelp.ipv4_address
  description = "Droplet public IP"
}

output "kelp_url" {
  value       = "https://kelp.${var.domain}"
  description = "KELP web URL"
}
