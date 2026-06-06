variable "vault_addr" {
  description = "Vault server address"
  type        = string
}

variable "proxmox_ip" {
  description = "Proxmox IP address"
  type        = string
  default     = "192.168.0.20"
}
variable "proxmox_port" {
  description = "Proxmox port number"
  type        = string
  default     = "8006"
}
variable "target_node" {
  description = "Proxmox node name"
  type        = string
  default     = "proxmoxserver"
}
variable "bridge_name" {
  description = "Network bridge"
  type        = string
  default     = "vmbr0"
}
variable "api_container_ip" {
  description = "API container IP address"
  type        = string
  default     = "192.168.0.18"
}
variable "db_container_ip" {
  description = "MariaDB container IP address"
  type        = string
  default     = "192.168.0.19"
}
