# 🚀 POC 3 en AWS - Guía Rápida

## ⚡ **Despliegue en 3 Pasos**

### **1. Configurar AWS CLI**
```bash
aws configure
aws sts get-caller-identity
```

### **2. Configurar Variables**
```bash
# Copiar archivo de ejemplo
cp env.prod.example .env.prod

# Editar variables (IMPORTANTE: cambiar valores por defecto)
nano .env.prod
```

### **3. Desplegar**
```bash
# Despliegue completo automático
./scripts/deploy-aws.sh prod us-east-1
```

## 🎯 **¿Qué se Despliega?**

### **Infraestructura AWS:**
- ✅ **VPC** con subnets públicas/privadas
- ✅ **ECS Fargate** para contenedores sin servidor
- ✅ **RDS PostgreSQL** para base de datos
- ✅ **ElastiCache Redis** para cache
- ✅ **Application Load Balancer** para tráfico
- ✅ **Secrets Manager** para credenciales
- ✅ **CloudWatch** para logs y métricas

### **Servicios de la Aplicación:**
- ✅ **POC 3 Security API** con JWT y MFA
- ✅ **Swagger UI** para documentación
- ✅ **Health Check** para monitoreo
- ✅ **Prometheus** para métricas
- ✅ **Grafana** para dashboards

## 🌐 **URLs Después del Despliegue**

```bash
# Obtener URL del ALB
ALB_DNS=$(terraform output -raw alb_dns_name)

# URLs principales
echo "🌐 API: http://$ALB_DNS"
echo "📚 Swagger: http://$ALB_DNS/docs"
echo "🏥 Health: http://$ALB_DNS/health"
```

## 🧪 **Probar la API**

### **1. Login**
```bash
curl -X POST "http://$ALB_DNS/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### **2. Crear Cliente**
```bash
TOKEN="tu_token_aqui"
curl -X POST "http://$ALB_DNS/customers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "email": "alice@example.com", "phone": "+57-300-123-4567"}'
```

## 📊 **Monitoreo**

### **Ver Logs**
```bash
aws logs tail /ecs/poc3-security-prod --follow
```

### **Ver Servicios**
```bash
aws ecs list-services --cluster poc3-security-prod-cluster
```

### **Dashboard CloudWatch**
```bash
# Abrir en navegador
open "https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=poc3-security-prod-dashboard"
```

## 💰 **Costos Estimados**

- **ECS Fargate**: ~$30-50/mes
- **RDS PostgreSQL**: ~$25-40/mes
- **ElastiCache Redis**: ~$15-25/mes
- **Application Load Balancer**: ~$20/mes
- **CloudWatch Logs**: ~$5-10/mes
- **Total**: ~$95-145/mes

## 🧹 **Limpiar Recursos**

```bash
# Destruir toda la infraestructura
cd terraform
terraform destroy -var-file="terraform.tfvars"
```

## 🔧 **Troubleshooting**

### **Problema: Health check falla**
```bash
# Ver logs del servicio
aws logs tail /ecs/poc3-security-prod --follow

# Ver estado de las tareas
aws ecs list-tasks --cluster poc3-security-prod-cluster
```

### **Problema: No se puede conectar a la API**
```bash
# Verificar security groups
aws ec2 describe-security-groups --group-ids $(aws ec2 describe-security-groups --filters "Name=group-name,Values=poc3-security-prod-*" --query 'SecurityGroups[0].GroupId' --output text)
```

## 📚 **Documentación Completa**

- **Guía Detallada**: [AWS_DEPLOYMENT_GUIDE.md](./AWS_DEPLOYMENT_GUIDE.md)
- **Explicación MFA**: [MFA_POC3_EXPLICACION.md](./MFA_POC3_EXPLICACION.md)
- **Swagger UI**: `http://your-alb-dns/docs`

## 🆘 **Soporte**

Si tienes problemas:
1. Revisa los logs: `aws logs tail /ecs/poc3-security-prod --follow`
2. Verifica el estado: `aws ecs describe-services --cluster poc3-security-prod-cluster`
3. Consulta la documentación completa en `AWS_DEPLOYMENT_GUIDE.md`

---

**🚀 ¡POC 3 desplegado exitosamente en AWS!**
