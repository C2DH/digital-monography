data "aws_secretsmanager_secret" "github_api_token" {
  name = "dgtmon-dev-github-api-token"
}

data "aws_secretsmanager_secret_version" "github_api_token" {
  secret_id = data.aws_secretsmanager_secret.github_api_token.id
}
