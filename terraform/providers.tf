terraform {
  required_providers {
    proxmox = {
      source  = "Telmate/proxmox"
      version = "3.0.2-rc07"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 5.9"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.19.1"
    }
  }
}

provider "vault" {
  address           = "https://vault.downops.win"
  skip_child_token  = true
}

data "vault_kv_secret_v2" "backend" {
  mount = "secret"
  name  = "wallet-tracker/backend"
}
data "vault_kv_secret_v2" "app" {
  mount = "secret"
  name  = "wallet-tracker/app"
}

provider "cloudflare" {
  api_token = data.vault_kv_secret_v2.backend.data["CLOUDFLARE_API_TOKEN"]
}

provider "proxmox" {
  pm_api_url      = "https://${var.proxmox_ip}:${var.proxmox_port}/api2/json"
  pm_user         = "${data.vault_kv_secret_v2.backend.data["PROXMOX_USER"]}@pam"
  pm_password     = data.vault_kv_secret_v2.backend.data["PROXMOX_PASSWORD"]
  pm_tls_insecure = true
}
