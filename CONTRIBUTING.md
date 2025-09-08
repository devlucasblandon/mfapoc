# Guía de Contribución

¡Gracias por tu interés en contribuir a MediSupply POCs! 🚀

## 🚀 Cómo Contribuir

### 1. Fork del Repositorio
- Haz fork de este repositorio
- Clona tu fork localmente
- Crea una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`

### 2. Desarrollo
- Sigue las convenciones de código existentes
- Asegúrate de que todas las pruebas pasen
- Agrega pruebas para nuevas funcionalidades
- Actualiza la documentación si es necesario

### 3. Testing
Antes de hacer commit, ejecuta las pruebas:

```bash
# Pruebas básicas
make test-poc3-all

# Pruebas de regresión
./scripts/poc3_regression_test.sh

# Pruebas de carga
./scripts/postman_poc3_load.sh
```

### 4. Commit y Push
```bash
git add .
git commit -m "feat: descripción de tu cambio"
git push origin feature/nueva-funcionalidad
```

### 5. Pull Request
- Crea un Pull Request desde tu fork
- Describe claramente los cambios realizados
- Asegúrate de que el CI/CD pase

## 📋 Convenciones

### Commits
Usa el formato conventional commits:
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` cambios en documentación
- `test:` agregar o modificar pruebas
- `refactor:` refactoring de código
- `perf:` mejoras de rendimiento

### Código
- Usa Python 3.8+
- Sigue PEP 8 para Python
- Documenta funciones y clases
- Agrega type hints cuando sea posible

### Pruebas
- Mantén cobertura de pruebas alta
- Agrega pruebas para casos límite
- Incluye pruebas de seguridad para POC3
- Documenta casos de prueba complejos

## 🐛 Reportar Issues

Al reportar un issue, incluye:
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Información del entorno (OS, versión de Python, etc.)
- Logs relevantes

## 🔒 Seguridad

Para reportar vulnerabilidades de seguridad:
- NO crees un issue público
- Envía un email a: security@medisupply.com
- Incluye detalles técnicos del problema
- Espera confirmación antes de hacer público

## 📚 Documentación

- Mantén el README actualizado
- Documenta nuevas APIs
- Actualiza guías de testing
- Incluye ejemplos de uso

## 🤝 Código de Conducta

- Sé respetuoso y constructivo
- Ayuda a otros contribuidores
- Mantén discusiones técnicas
- Respeta las decisiones del equipo

## 📞 Contacto

- Issues: Usa GitHub Issues
- Discusiones: GitHub Discussions
- Email: dev@medisupply.com

¡Gracias por contribuir! 🎉
