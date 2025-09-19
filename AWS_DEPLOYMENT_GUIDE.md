# 🚀 Guía de Despliegue POC 3 en AWS

## 📋 Índice
1. [Prerrequisitos](#prerrequisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Despliegue Automático](#despliegue-automático)
4. [Despliegue Manual](#despliegue-manual)
5. [Verificación](#verificación)
6. [Monitoreo](#monitoreo)
7. [Troubleshooting](#troubleshooting)
8. [Costos](#costos)
9. [Cleanup](#cleanup)

---

## Prerrequisitos

### **1. Herramientas Requeridas**
```bash
# AWS CLI
aws --version  # Debe ser >= 2.0

# Docker
docker --version  # Debe ser >= 20.0

# Terraform
terraform --version  # Debe ser >= 1.0

# Git
git --version
```

### **2. Cuenta AWS**
- Cuenta AWS activa
- Permisos de administrador o equivalentes
- Límites de servicio adecuados

### **3. Configuración AWS CLI**
```bash
# Configurar AWS CLI
aws configure

# Verificar configuración
aws sts get-caller-identity
```

---

## Configuración Inicial

### **1. Clonar Repositorio**
```bash
git clone https://github.com/medisupply/medisupply-pocs-with-postman-k6-ci-newman.git
cd medisupply-pocs-with-postman-k6-ci-newman
```

### **2. Configurar Variables de Entorno**
```bash
# Copiar archivo de ejemplo
cp env.prod.example .env.prod

# Editar variables
nano .env.prod
```

### **3. Variables Importantes**
```bash
# Cambiar estos valores en producción
DB_PASSWORD=your_secure_db_password_here
JWT_SECRET_KEY=your_super_secure_jwt_secret_key_here
ENCRYPTION_KEY=your_32_character_encryption_key_here
GRAFANA_PASSWORD=your_grafana_admin_password_here
```

---

## Despliegue Automático

### **Opción 1: Script de Despliegue (Recomendado)**
```bash
# Despliegue completo
./scripts/deploy-aws.sh prod us-east-1

# Despliegue en otra región
./scripts/deploy-aws.sh prod eu-west-1
```

### **Opción 2: Despliegue por Pasos**
```bash
# 1. Crear ECR Repository
aws ecr create-repository --repository-name poc3-security-prod --region us-east-1

# 2. Login a ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# 3. Construir y subir imagen
docker build -f Dockerfile.poc3.prod -t poc3-security-prod .
docker tag poc3-security-prod:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/poc3-security-prod:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/poc3-security-prod:latest

# 4. Desplegar infraestructura
cd terraform
terraform init
terraform plan
terraform apply
```

---

## Despliegue Manual

### **1. Infraestructura con Terraform**
```bash
cd terraform

# Inicializar
terraform init

# Crear variables
cat > terraform.tfvars << EOF
aws_region   = "us-east-1"
environment  = "prod"
project_name = "poc3-security"
aws_account_id = "123456789012"
EOF

# Plan
terraform plan -var-file="terraform.tfvars"

# Aplicar
terraform apply -var-file="terraform.tfvars"
```

### **2. Servicios AWS Creados**
- **VPC** con subnets públicas y privadas
- **ECS Cluster** con Fargate
- **RDS PostgreSQL** para base de datos
- **ElastiCache Redis** para cache
- **Application Load Balancer** para tráfico
- **Secrets Manager** para credenciales
- **CloudWatch** para logs y métricas

---

## Verificación

### **1. Health Check**
```bash
# Obtener URL del ALB
ALB_DNS=$(terraform output -raw alb_dns_name)

# Verificar health
curl http://$ALB_DNS/health
```

### **2. Swagger UI**
```bash
# Abrir Swagger UI
open http://$ALB_DNS/docs
```

### **3. Pruebas de API**
```bash
# Login
curl -X POST "http://$ALB_DNS/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Crear cliente
curl -X POST "http://$ALB_DNS/customers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "email": "alice@example.com", "phone": "+57-300-123-4567"}'
```

---

## Monitoreo

### **1. CloudWatch Logs**
```bash
# Ver logs en tiempo real
aws logs tail /ecs/poc3-security-prod --follow

# Ver logs específicos
aws logs get-log-events --log-group-name /ecs/poc3-security-prod --log-stream-name ecs/poc3-security-prod-container/1234567890
```

### **2. ECS Console**
```bash
# Ver servicios
aws ecs list-services --cluster poc3-security-prod-cluster

# Ver tareas
aws ecs list-tasks --cluster poc3-security-prod-cluster

# Ver detalles de tarea
aws ecs describe-tasks --cluster poc3-security-prod-cluster --tasks arn:aws:ecs:us-east-1:123456789012:task/poc3-security-prod-cluster/1234567890
```

### **3. Métricas**
- **CPU/Memory** en CloudWatch
- **Request Count** en ALB
- **Database Connections** en RDS
- **Cache Hit Rate** en Redis

---

## Troubleshooting

### **1. Problemas Comunes**

#### **Error: "No space left on device"**
```bash
# Limpiar imágenes Docker
docker system prune -a

# Verificar espacio
df -h
```

#### **Error: "Task failed to start"**
```bash
# Verificar logs
aws logs tail /ecs/poc3-security-prod --follow

# Verificar configuración de tarea
aws ecs describe-task-definition --task-definition poc3-security-prod-task
```

#### **Error: "Health check failed"**
```bash
# Verificar security groups
aws ec2 describe-security-groups --group-ids sg-1234567890abcdef0

# Verificar connectivity
aws ecs describe-tasks --cluster poc3-security-prod-cluster --tasks arn:aws:ecs:us-east-1:123456789012:task/poc3-security-prod-cluster/1234567890
```

### **2. Comandos de Diagnóstico**
```bash
# Estado del cluster
aws ecs describe-clusters --clusters poc3-security-prod-cluster

# Estado del servicio
aws ecs describe-services --cluster poc3-security-prod-cluster --services poc3-security-prod-service

# Estado de las tareas
aws ecs describe-tasks --cluster poc3-security-prod-cluster --tasks $(aws ecs list-tasks --cluster poc3-security-prod-cluster --query 'taskArns[0]' --output text)
```

---

## Costos

### **1. Estimación Mensual (us-east-1)**
- **ECS Fargate**: ~$30-50/mes
- **RDS PostgreSQL**: ~$25-40/mes
- **ElastiCache Redis**: ~$15-25/mes
- **Application Load Balancer**: ~$20/mes
- **CloudWatch Logs**: ~$5-10/mes
- **Total**: ~$95-145/mes

### **2. Optimizaciones de Costo**
- Usar **t3.micro** para RDS en desarrollo
- Configurar **auto-scaling** para ECS
- Usar **Spot Instances** para tareas no críticas
- Configurar **retention policies** para logs

---

## Cleanup

### **1. Destruir Infraestructura**
```bash
cd terraform
terraform destroy -var-file="terraform.tfvars"
```

### **2. Limpiar ECR**
```bash
# Eliminar imágenes
aws ecr batch-delete-image --repository-name poc3-security-prod --image-ids imageTag=latest

# Eliminar repository
aws ecr delete-repository --repository-name poc3-security-prod --force
```

### **3. Limpiar Docker Local**
```bash
# Eliminar imágenes locales
docker rmi poc3-security-prod:latest
docker rmi 123456789012.dkr.ecr.us-east-1.amazonaws.com/poc3-security-prod:latest

# Limpiar sistema
docker system prune -a
```

---

## 🎯 **Resumen**

### **✅ Lo que se despliega:**
1. **VPC** completa con subnets públicas/privadas
2. **ECS Cluster** con Fargate para contenedores
3. **RDS PostgreSQL** para base de datos
4. **ElastiCache Redis** para cache
5. **Application Load Balancer** para tráfico
6. **Secrets Manager** para credenciales
7. **CloudWatch** para monitoreo

### **🔧 Comandos Principales:**
```bash
# Despliegue completo
./scripts/deploy-aws.sh prod us-east-1

# Ver logs
aws logs tail /ecs/poc3-security-prod --follow

# Destruir todo
cd terraform && terraform destroy -var-file="terraform.tfvars"
```

### **🌐 URLs Después del Despliegue:**
- **API**: `http://your-alb-dns-name`
- **Swagger**: `http://your-alb-dns-name/docs`
- **Health**: `http://your-alb-dns-name/health`

---

**📅 Fecha de Creación:** 18 de Septiembre de 2025  
**👨‍💻 Autor:** Equipo de Desarrollo MediSupply  
**📝 Versión:** 1.0.0  
**🔗 Repositorio:** [medisupply-pocs-with-postman-k6-ci-newman](https://github.com/medisupply/medisupply-pocs-with-postman-k6-ci-newman)
