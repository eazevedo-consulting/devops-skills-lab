# Main entry point for Infrastructure on Demand

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  backend "azurerm" {} # Remote state must be configured for each run
}

provider "azurerm" {
  features {}
}

module "resource_group" {
  source   = "./modules/resource_group"
  name     = var.env_name
  location = var.region
}

module "network" {
  source   = "./modules/network"
  rg_name  = module.resource_group.name
  location = module.resource_group.location
}

module "storage" {
  count    = var.create_storage ? 1 : 0
  source   = "./modules/storage"
  name     = "${var.env_name}-sa"
  rg_name  = module.resource_group.name
  location = module.resource_group.location
}

module "vm" {
  count      = var.create_vm ? 1 : 0
  source     = "./modules/vm"
  name       = "${var.env_name}-vm"
  rg_name    = module.resource_group.name
  location   = module.resource_group.location
  subnet_id  = module.network.subnet_id
  public_key = var.ssh_public_key
}
