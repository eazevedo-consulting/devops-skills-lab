# Terraform configuration for local VM cluster management
resource "null_resource" "cluster_provisioner" {
  provisioner "local-exec" {
    command = "vagrant up"
  }
}

output "master_ip" {
  value = "192.168.56.10"
}
