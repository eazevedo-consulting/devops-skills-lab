variable "env_name" { type = string }
variable "region" { type = string }
variable "create_storage" { type = bool; default = false }
variable "create_vm" { type = bool; default = false }
variable "ssh_public_key" { type = string; default = "" }
