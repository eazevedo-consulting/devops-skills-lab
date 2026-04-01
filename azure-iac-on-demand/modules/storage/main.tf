resource "azurerm_storage_account" "sa" {
  name                     = lower(replace(var.name, "-", ""))
  resource_group_name      = var.rg_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

output "id" {
  value = azurerm_storage_account.sa.id
}
