# Módulo Secrets Manager para POC 3
resource "aws_secretsmanager_secret" "db_url" {
  name                    = "${var.project_name}-${var.environment}-db-url"
  description             = "Database URL for POC 3"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-url"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "db_url" {
  secret_id = aws_secretsmanager_secret.db_url.id
  secret_string = jsonencode({
    username = "poc3_user"
    password = var.db_password
    host     = var.rds_endpoint
    port     = 5432
    database = "poc3_db"
    url      = "postgresql://poc3_user:${var.db_password}@${var.rds_endpoint}:5432/poc3_db"
  })
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.project_name}-${var.environment}-jwt-secret"
  description             = "JWT Secret Key for POC 3"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-jwt-secret"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id = aws_secretsmanager_secret.jwt_secret.id
  secret_string = jsonencode({
    secret = var.jwt_secret_key
  })
}

resource "aws_secretsmanager_secret" "encryption_key" {
  name                    = "${var.project_name}-${var.environment}-encryption-key"
  description             = "Encryption Key for POC 3"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-encryption-key"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "encryption_key" {
  secret_id = aws_secretsmanager_secret.encryption_key.id
  secret_string = jsonencode({
    key = var.encryption_key
  })
}

resource "aws_secretsmanager_secret" "redis_url" {
  name                    = "${var.project_name}-${var.environment}-redis-url"
  description             = "Redis URL for POC 3"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis-url"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "redis_url" {
  secret_id = aws_secretsmanager_secret.redis_url.id
  secret_string = jsonencode({
    host = var.redis_endpoint
    port = 6379
    url  = "redis://${var.redis_endpoint}:6379/0"
  })
}

# Variables
variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
}

variable "environment" {
  description = "Ambiente"
  type        = string
}

variable "db_password" {
  description = "Contraseña de la base de datos"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT Secret Key"
  type        = string
  sensitive   = true
}

variable "encryption_key" {
  description = "Encryption Key"
  type        = string
  sensitive   = true
}

variable "rds_endpoint" {
  description = "Endpoint de RDS"
  type        = string
}

variable "redis_endpoint" {
  description = "Endpoint de Redis"
  type        = string
}

# Outputs
output "db_url_secret_arn" {
  description = "ARN del secret de DB URL"
  value       = aws_secretsmanager_secret.db_url.arn
}

output "jwt_secret_arn" {
  description = "ARN del secret de JWT"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "encryption_key_arn" {
  description = "ARN del secret de Encryption Key"
  value       = aws_secretsmanager_secret.encryption_key.arn
}

output "redis_url_secret_arn" {
  description = "ARN del secret de Redis URL"
  value       = aws_secretsmanager_secret.redis_url.arn
}
