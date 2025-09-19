# Terraform para POC 3 en AWS
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "poc3-security"
}

variable "aws_account_id" {
  description = "ID de la cuenta de AWS"
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

# VPC y Networking
module "vpc" {
  source = "./modules/vpc"
  
  project_name = var.project_name
  environment  = var.environment
}

# RDS PostgreSQL
module "rds" {
  source = "./modules/rds"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids
  security_group_id = module.vpc.rds_security_group_id
  db_password = var.db_password
}

# ElastiCache Redis
module "redis" {
  source = "./modules/redis"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids
  security_group_id = module.vpc.redis_security_group_id
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.public_subnet_ids
  ecs_security_group_id = module.vpc.ecs_security_group_id
  target_group_arn = module.alb.target_group_arn
  alb_listener_arn = module.alb.listener_arn
  aws_region = var.aws_region
  aws_account_id = var.aws_account_id
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.public_subnet_ids
  security_group_id = module.vpc.alb_security_group_id
}

# Secrets Manager
module "secrets" {
  source = "./modules/secrets"
  
  project_name = var.project_name
  environment  = var.environment
  db_password = var.db_password
  jwt_secret_key = var.jwt_secret_key
  encryption_key = var.encryption_key
  rds_endpoint = module.rds.rds_endpoint
  redis_endpoint = module.redis.redis_endpoint
}

# CloudWatch Logs
module "cloudwatch" {
  source = "./modules/cloudwatch"
  
  project_name = var.project_name
  environment  = var.environment
  aws_region = var.aws_region
}

# Outputs
output "vpc_id" {
  description = "ID de la VPC"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "DNS del Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "rds_endpoint" {
  description = "Endpoint de RDS"
  value       = module.rds.rds_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Endpoint de Redis"
  value       = module.redis.redis_endpoint
  sensitive   = true
}
