output "server_ip" {
  value       = hcloud_server.kelp.ipv4_address
  description = "Server public IP"
}

output "kelp_url" {
  value       = "https://kelp.${var.domain}"
  description = "KELP web URL"
}

output "dns_instructions" {
  value       = "Update A record for kelp.${var.domain} to ${hcloud_server.kelp.ipv4_address} in Namecheap DNS"
  description = "DNS update instructions"
}
