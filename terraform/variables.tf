variable "region" { default = "eu-central-1" }
variable "deploy_app" { default = false }
variable "image_tag" { default = "v1" }
variable "openai_model" { default = "gpt-4.1-mini" }
variable "min_tasks" {
  default = 2
  validation {
    condition     = var.min_tasks >= 1 && var.min_tasks <= 4
    error_message = "Choose between one and four tasks. Two is the availability baseline."
  }
}
