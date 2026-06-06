terraform {
  required_providers {
    proxmox = {
      source  = "Telmate/proxmox"
      version = "3.0.2-rc07"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.19.1"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.0"
    }
  }
}

provider "vault" {
  address = var.vault_addr
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
