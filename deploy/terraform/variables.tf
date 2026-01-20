variable "do_token" {
  description = "Digital Ocean API token"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DO region"
  type        = string
  default     = "nyc1"
}

variable "ssh_key_name" {
  description = "Name of existing SSH key in Digital Ocean"
  type        = string
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key"
  type        = string
  default     = "~/.ssh/id_ed25519"
}

variable "domain" {
  description = "Domain name registered in DO"
  type        = string
  default     = "vroblok.io"
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed to SSH (e.g., [\"1.2.3.4/32\"] for single IP)"
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]  # Open by default, override in tfvars
}
