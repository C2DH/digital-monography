resource "aws_api_gateway_rest_api" "general_api" {
  name = "${var.project}-${var.env}-${var.general_rest_api_gateway}"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.general_api.id
  parent_id   = aws_api_gateway_rest_api.general_api.root_resource_id
  path_part   = "{proxy+}"
}

# resource "aws_api_gateway_resource" "orm" {
#   rest_api_id = aws_api_gateway_rest_api.general_api.id
#   parent_id   = aws_api_gateway_rest_api.general_api.root_resource_id
#   path_part   = "api"
# }

resource "aws_api_gateway_resource" "entrypoint" {
  rest_api_id = aws_api_gateway_rest_api.general_api.id
  parent_id   = aws_api_gateway_rest_api.general_api.root_resource_id
  path_part   = "dbx"
}

resource "aws_api_gateway_resource" "gpu" {
  rest_api_id = aws_api_gateway_rest_api.general_api.id
  parent_id   = aws_api_gateway_rest_api.general_api.root_resource_id
  path_part   = "gpu"
}

# Lambda permissions
resource "aws_lambda_permission" "entrypoint" {
  statement_id  = "AllowAPIGatewayInvokeEntrypoint"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.entrypoint_func.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.general_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "gpu" {
  statement_id  = "AllowAPIGatewayInvokeGPU"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gpu_func.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.general_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "orm" {
  statement_id  = "AllowAPIGatewayInvokeORM"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orm_func.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.general_api.execution_arn}/*/*"
}

# Method and Integration for root ANY -> Lambda-entrypoint
resource "aws_api_gateway_method" "root_any" {
  rest_api_id   = aws_api_gateway_rest_api.general_api.id
  resource_id   = aws_api_gateway_rest_api.general_api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root_any" {
  rest_api_id             = aws_api_gateway_rest_api.general_api.id
  resource_id             = aws_api_gateway_rest_api.general_api.root_resource_id
  http_method             = aws_api_gateway_method.root_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.orm_func.invoke_arn
}

# Method and Integration for /{proxy+} -> Lambda-entrypoint
resource "aws_api_gateway_method" "proxy_any" {
  rest_api_id   = aws_api_gateway_rest_api.general_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy_any" {
  rest_api_id             = aws_api_gateway_rest_api.general_api.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.orm_func.invoke_arn
}

# Method and Integration for /gpu -> Lambda-gpu
resource "aws_api_gateway_method" "gpu_any" {
  rest_api_id   = aws_api_gateway_rest_api.general_api.id
  resource_id   = aws_api_gateway_resource.gpu.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "gpu_any" {
  rest_api_id             = aws_api_gateway_rest_api.general_api.id
  resource_id             = aws_api_gateway_resource.gpu.id
  http_method             = aws_api_gateway_method.gpu_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.gpu_func.invoke_arn
}

# Method and Integration for /dbx -> Lambda-orm
resource "aws_api_gateway_method" "entrypoint_any" {
  rest_api_id   = aws_api_gateway_rest_api.general_api.id
  resource_id   = aws_api_gateway_resource.entrypoint.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "entrypoint_any" {
  rest_api_id             = aws_api_gateway_rest_api.general_api.id
  resource_id             = aws_api_gateway_resource.entrypoint.id
  http_method             = aws_api_gateway_method.entrypoint_any.http_method
  integration_http_method = "POST" # Lambda function can only be invoked via POST
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.entrypoint_func.invoke_arn
}

# Deployment and Stage
resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    aws_api_gateway_integration.root_any,
    aws_api_gateway_integration.proxy_any,
    aws_api_gateway_integration.gpu_any,
    aws_api_gateway_integration.entrypoint_any
  ]
  rest_api_id = aws_api_gateway_rest_api.general_api.id
}

resource "aws_api_gateway_stage" "stage_test" {
  deployment_id = aws_api_gateway_deployment.deployment.id
  rest_api_id   = aws_api_gateway_rest_api.general_api.id
  stage_name    = var.env # should be "main" or "develop"
}

data "aws_caller_identity" "current" {}
