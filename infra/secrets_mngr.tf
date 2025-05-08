data "aws_secretsmanager_secret" "github_api_token" {
  name = var.secretsmanager_github_api_secrets
  # name = "dgtmon-dev-github-api-secrets"
}

data "aws_secretsmanager_secret_version" "github_api_token" {
  secret_id = data.aws_secretsmanager_secret.github_api_token.id
}
