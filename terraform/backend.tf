variable "api_hostname" {
  description = "API container hostname"
  type        = string
  default     = "backend.wallettracker.downops.win"
}

resource "proxmox_lxc" "api" {
  target_node = var.target_node
  hostname    = var.api_hostname
  ostemplate  = "local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz"
  password    = data.vault_kv_secret_v2.backend.data["BACKEND_CONTAINER_PASSWORD"]
  cores       = 1
  memory      = 512
  swap        = 512
  nameserver  = "8.8.8.8"
  rootfs {
    storage = "local-lvm"
    size    = "4G"
  }
  network {
    name   = "eth0"
    bridge = var.bridge_name
    gw     = "192.168.0.1"
    ip     = "${var.api_container_ip}/24"
  }
  start = true
  lifecycle {
    create_before_destroy = true
  }
}

resource "null_resource" "setup_api_in_container" {
  depends_on = [proxmox_lxc.api]

  connection {
    type     = "ssh"
    host     = var.proxmox_ip
    user     = data.vault_kv_secret_v2.backend.data["PROXMOX_USER"]
    password = data.vault_kv_secret_v2.backend.data["PROXMOX_PASSWORD"]
  }

  provisioner "file" {
    content     = <<-INITEOF
      #!/sbin/openrc-run
      description="WalletTracker uWSGI"

      VENV_PATH="/srv/WalletTrackerAPI/app/.venv"
      directory="/srv/WalletTrackerAPI/app"
      pidfile="/run/wallettracker.pid"
      command="$${VENV_PATH}/bin/uwsgi"
      command_args="--ini $${directory}/uwsgi.ini --logto2 /var/log/wallettracker.log"
      command_background="yes"

      export DATABASE_ROOT_PASSWORD="${data.vault_kv_secret_v2.backend.data["MARIADB_ROOT_PASSWORD"]}"
      export WALLET_TRACKER_DB_USER="root"
      export WALLET_TRACKER_DB_HOST="${var.db_container_ip}"
      export DATABASE_NAME="wallet_tracker"
      export WALLET_TRACKER_SECRET="${data.vault_kv_secret_v2.app.data["SIGN_SECRET_WORD"]}"
      export ENABLE_REGISTER="false"

      start_pre() {
        checkpath --directory --owner root:root $${pidfile%/*}
      }
      INITEOF
    destination = "/tmp/wallettracker.init"
  }

  provisioner "remote-exec" {
    inline = [
      <<-EOF
      set -ex
      pct exec ${proxmox_lxc.api.vmid} -- apk update
      pct exec ${proxmox_lxc.api.vmid} -- apk add --no-cache git python3 mariadb-dev gcc musl-dev python3-dev build-base linux-headers uv

      pct exec ${proxmox_lxc.api.vmid} -- git clone https://github.com/noelpatata/WalletTrackerAPI.git /srv/WalletTrackerAPI

      pct exec ${proxmox_lxc.api.vmid} -- uv sync --no-dev --frozen --directory /srv/WalletTrackerAPI/app

      pct exec ${proxmox_lxc.api.vmid} -- apk del gcc musl-dev build-base linux-headers

      pct exec ${proxmox_lxc.api.vmid} -- mkdir -p /var/logs
      pct exec ${proxmox_lxc.api.vmid} -- touch /var/log/wallettracker.log
      pct exec ${proxmox_lxc.api.vmid} -- chmod 644 /var/log/wallettracker.log

      pct push ${proxmox_lxc.api.vmid} /tmp/wallettracker.init /etc/init.d/wallettracker
      rm /tmp/wallettracker.init

      pct exec ${proxmox_lxc.api.vmid} -- chmod +x /etc/init.d/wallettracker
      pct exec ${proxmox_lxc.api.vmid} -- rc-update add wallettracker default
      pct exec ${proxmox_lxc.api.vmid} -- rc-service wallettracker start
      EOF
    ]
  }
}

resource "null_resource" "deploy_api" {
  depends_on = [null_resource.setup_api_in_container, null_resource.deploy_mariadb]

  triggers = {
    always_run = timestamp()
  }

  connection {
    type     = "ssh"
    host     = var.proxmox_ip
    user     = data.vault_kv_secret_v2.backend.data["PROXMOX_USER"]
    password = data.vault_kv_secret_v2.backend.data["PROXMOX_PASSWORD"]
  }

  provisioner "file" {
    content     = <<-INITEOF
      #!/sbin/openrc-run
      description="WalletTracker uWSGI"

      VENV_PATH="/srv/WalletTrackerAPI/app/.venv"
      directory="/srv/WalletTrackerAPI/app"
      pidfile="/run/wallettracker.pid"
      command="$${VENV_PATH}/bin/uwsgi"
      command_args="--ini $${directory}/uwsgi.ini --logto2 /var/log/wallettracker.log"
      command_background="yes"

      export DATABASE_ROOT_PASSWORD="${data.vault_kv_secret_v2.backend.data["MARIADB_ROOT_PASSWORD"]}"
      export WALLET_TRACKER_DB_USER="root"
      export WALLET_TRACKER_DB_HOST="${var.db_container_ip}"
      export DATABASE_NAME="wallet_tracker"
      export WALLET_TRACKER_SECRET="${data.vault_kv_secret_v2.app.data["SIGN_SECRET_WORD"]}"
      export ENABLE_REGISTER="false"

      start_pre() {
        checkpath --directory --owner root:root $${pidfile%/*}
      }
      INITEOF
    destination = "/tmp/wallettracker.init"
  }

  provisioner "remote-exec" {
    inline = [
      <<-EOF
      set -ex
      pct exec ${proxmox_lxc.api.vmid} -- git -C /srv/WalletTrackerAPI pull

      pct exec ${proxmox_lxc.api.vmid} -- uv sync --no-dev --frozen --directory /srv/WalletTrackerAPI/app

      pct exec ${proxmox_lxc.api.vmid} -- sh -c "export DATABASE_ROOT_PASSWORD='${data.vault_kv_secret_v2.backend.data["MARIADB_ROOT_PASSWORD"]}'; export DATABASE_NAME='wallet_tracker'; export WALLET_TRACKER_DB_USER='root'; export WALLET_TRACKER_DB_HOST='${var.db_container_ip}'; /srv/WalletTrackerAPI/app/.venv/bin/python /srv/WalletTrackerAPI/app/migrate_all.py"

      pct push ${proxmox_lxc.api.vmid} /tmp/wallettracker.init /etc/init.d/wallettracker
      rm /tmp/wallettracker.init
      pct exec ${proxmox_lxc.api.vmid} -- chmod +x /etc/init.d/wallettracker

      pct exec ${proxmox_lxc.api.vmid} -- rc-service wallettracker restart
      EOF
    ]
  }
}

output "api_container" {
  value = proxmox_lxc.api.hostname
}
