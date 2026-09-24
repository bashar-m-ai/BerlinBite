output "app_url" { value = "https://${aws_cloudfront_distribution.app.domain_name}" }
output "repository_url" { value = aws_ecr_repository.app.repository_url }
output "google_secret_arn" { value = aws_secretsmanager_secret.google.arn }
output "openai_secret_arn" { value = aws_secretsmanager_secret.openai.arn }
