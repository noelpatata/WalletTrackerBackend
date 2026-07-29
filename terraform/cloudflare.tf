variable "api_public_hostname" {
  description = "Public hostname for the API (e.g. api.downops.win)"
  type        = string
  default     = "api.downops.win"
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "api" {
  account_id = data.vault_kv_secret_v2.common.data["CLOUDFLARE_ACCOUNT_ID"]
  name       = "wallettracker-api"
  depends_on = [null_resource.deploy_api]
}

data "cloudflare_zero_trust_tunnel_cloudflared_token" "api" {
  account_id = data.vault_kv_secret_v2.common.data["CLOUDFLARE_ACCOUNT_ID"]
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.api.id
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "api" {
  account_id = data.vault_kv_secret_v2.common.data["CLOUDFLARE_ACCOUNT_ID"]
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.api.id

  config = {
    ingress = [
      {
        hostname = var.api_public_hostname
        service  = "http://localhost:5000"
      },
      {
        service = "http_status:404"
      }
    ]
  }
}

resource "cloudflare_dns_record" "api" {
  zone_id = data.vault_kv_secret_v2.app.data["CLOUDFLARE_ZONE_ID"]
  name    = "api"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.api.id}.cfargotunnel.com"
  type    = "CNAME"
  ttl     = 1
  proxied = true
  lifecycle {
    create_before_destroy = false
  }
}

resource "null_resource" "setup_cloudflared" {
  depends_on = [null_resource.deploy_api, cloudflare_zero_trust_tunnel_cloudflared.api]

  connection {
    type     = "ssh"
    host     = var.proxmox_ip
    user     = data.vault_kv_secret_v2.common.data["PROXMOX_USER"]
    password = data.vault_kv_secret_v2.common.data["PROXMOX_PASSWORD"]
  }

  provisioner "file" {
    content     = <<-INITEOF
      #!/sbin/openrc-run
      name="cloudflared"
      description="Cloudflare Tunnel"
      command="/usr/bin/cloudflared"
      command_args="tunnel run --token ${data.cloudflare_zero_trust_tunnel_cloudflared_token.api.token}"
      command_background=true
      pidfile="/run/cloudflared.pid"
      output_log="/var/log/cloudflared.log"
      error_log="/var/log/cloudflared.log"

      depend() {
        need net
        after wallettracker
      }
      INITEOF
    destination = "/tmp/cloudflared.init"
  }

  provisioner "remote-exec" {
    inline = [
      <<-EOF
      pct exec ${proxmox_lxc.api.vmid} -- wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/bin/cloudflared
      pct exec ${proxmox_lxc.api.vmid} -- chmod +x /usr/bin/cloudflared

      pct push ${proxmox_lxc.api.vmid} /tmp/cloudflared.init /etc/init.d/cloudflared
      rm /tmp/cloudflared.init

      pct exec ${proxmox_lxc.api.vmid} -- chmod +x /etc/init.d/cloudflared
      pct exec ${proxmox_lxc.api.vmid} -- rc-update add cloudflared default
      pct exec ${proxmox_lxc.api.vmid} -- rc-service cloudflared start
      EOF
    ]
  }
}

output "api_public_url" {
  value = "https://${var.api_public_hostname}"
}
