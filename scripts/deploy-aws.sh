#!/bin/bash

# Script de Despliegue para POC 3 en AWS
# Uso: ./scripts/deploy-aws.sh [environment] [region]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
}

# Variables
ENVIRONMENT=${1:-prod}
AWS_REGION=${2:-us-east-1}
PROJECT_NAME="poc3-security"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Validar que AWS CLI esté configurado
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    error "AWS CLI no está configurado. Ejecuta 'aws configure' primero."
    exit 1
fi

log "Iniciando despliegue de POC 3 en AWS"
log "Ambiente: $ENVIRONMENT"
log "Región: $AWS_REGION"
log "Cuenta AWS: $AWS_ACCOUNT_ID"

# Paso 1: Crear ECR Repository
log "Paso 1: Creando ECR Repository..."
aws ecr describe-repositories --repository-name $PROJECT_NAME-$ENVIRONMENT --region $AWS_REGION > /dev/null 2>&1 || {
    aws ecr create-repository --repository-name $PROJECT_NAME-$ENVIRONMENT --region $AWS_REGION
    success "ECR Repository creado: $PROJECT_NAME-$ENVIRONMENT"
}

# Paso 2: Login a ECR
log "Paso 2: Haciendo login a ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
success "Login a ECR exitoso"

# Paso 3: Construir imagen Docker
log "Paso 3: Construyendo imagen Docker..."
docker build -f Dockerfile.poc3.prod -t $PROJECT_NAME-$ENVIRONMENT .
success "Imagen Docker construida"

# Paso 4: Taggear imagen para ECR
log "Paso 4: Taggeando imagen para ECR..."
docker tag $PROJECT_NAME-$ENVIRONMENT:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT:latest
success "Imagen taggeada para ECR"

# Paso 5: Subir imagen a ECR
log "Paso 5: Subiendo imagen a ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT:latest
success "Imagen subida a ECR"

# Paso 6: Desplegar infraestructura con Terraform
log "Paso 6: Desplegando infraestructura con Terraform..."
cd terraform

# Inicializar Terraform
terraform init

# Crear archivo de variables
cat > terraform.tfvars << EOF
aws_region   = "$AWS_REGION"
environment  = "$ENVIRONMENT"
project_name = "$PROJECT_NAME"
aws_account_id = "$AWS_ACCOUNT_ID"
EOF

# Plan de Terraform
log "Ejecutando terraform plan..."
terraform plan -var-file="terraform.tfvars"

# Aplicar Terraform
log "Ejecutando terraform apply..."
terraform apply -var-file="terraform.tfvars" -auto-approve

success "Infraestructura desplegada con Terraform"

# Paso 7: Obtener URL del ALB
log "Paso 7: Obteniendo URL del Application Load Balancer..."
ALB_DNS=$(terraform output -raw alb_dns_name)
success "ALB DNS: $ALB_DNS"

# Paso 8: Verificar despliegue
log "Paso 8: Verificando despliegue..."
sleep 30  # Esperar a que el servicio esté listo

# Health check
log "Ejecutando health check..."
if curl -f "http://$ALB_DNS/health" > /dev/null 2>&1; then
    success "Health check exitoso"
    success "POC 3 desplegado exitosamente en AWS!"
    success "URL: http://$ALB_DNS"
    success "Swagger UI: http://$ALB_DNS/docs"
    success "Health Check: http://$ALB_DNS/health"
else
    warning "Health check falló. Verifica los logs del servicio ECS."
    log "Puedes ver los logs con: aws logs tail /ecs/$PROJECT_NAME-$ENVIRONMENT --follow"
fi

# Paso 9: Mostrar información útil
log "Paso 9: Información del despliegue..."
echo ""
echo "=========================================="
echo "🚀 POC 3 DESPLEGADO EN AWS"
echo "=========================================="
echo "🌐 URL Principal: http://$ALB_DNS"
echo "📚 Swagger UI: http://$ALB_DNS/docs"
echo "🏥 Health Check: http://$ALB_DNS/health"
echo "📊 Grafana: http://$ALB_DNS:3000"
echo "🔍 Prometheus: http://$ALB_DNS:9090"
echo ""
echo "📋 Comandos útiles:"
echo "  Ver logs: aws logs tail /ecs/$PROJECT_NAME-$ENVIRONMENT --follow"
echo "  Ver servicios: aws ecs list-services --cluster $PROJECT_NAME-$ENVIRONMENT-cluster"
echo "  Ver tareas: aws ecs list-tasks --cluster $PROJECT_NAME-$ENVIRONMENT-cluster"
echo "  Destruir: cd terraform && terraform destroy -var-file='terraform.tfvars'"
echo "=========================================="

success "Despliegue completado!"
