#!/bin/bash

# Script para ejecutar pruebas de JWT del POC3 con Newman
# Este script ejecuta la colección de Postman específica para JWT

set -e

echo "🔐 Iniciando pruebas de JWT del POC3 Security con Newman..."

# Verificar que Newman esté instalado
if ! command -v newman &> /dev/null; then
    echo "❌ Newman no está instalado. Instalando..."
    npm install -g newman
fi

# Verificar que el POC3 esté ejecutándose
echo "🔍 Verificando que POC3 esté ejecutándose..."
if ! curl -s http://localhost:8083/auth/demo-tokens > /dev/null; then
    echo "❌ POC3 no está ejecutándose en http://localhost:8083"
    echo "💡 Ejecuta 'make poc3' primero"
    exit 1
fi

echo "✅ POC3 está ejecutándose correctamente"

# Configuración de las pruebas
COLLECTION_FILE="postman/POC3_Security_JWT.postman_collection.json"
ENVIRONMENT_FILE="postman/environment.medisupply.local.json"
ITERATIONS=5
DELAY=1000

echo "📊 Configuración de las pruebas JWT:"
echo "   - Colección: $COLLECTION_FILE"
echo "   - Entorno: $ENVIRONMENT_FILE"
echo "   - Iteraciones: $ITERATIONS"
echo "   - Delay entre requests: ${DELAY}ms"
echo ""

# Función para ejecutar pruebas con diferentes configuraciones
run_jwt_test() {
    local test_name="$1"
    local iterations="$2"
    local delay="$3"
    
    echo "🔄 Ejecutando: $test_name"
    echo "   - Iteraciones: $iterations"
    echo "   - Delay entre requests: ${delay}ms"
    
    newman run "$COLLECTION_FILE" \
        --environment "$ENVIRONMENT_FILE" \
        --iteration-count "$iterations" \
        --delay-request "$delay" \
        --reporters cli,json \
        --reporter-json-export "results/poc3_jwt_${test_name// /_}_$(date +%Y%m%d_%H%M%S).json" \
        --suppress-exit-code
}

# Crear directorio de resultados
mkdir -p results

echo "🏁 Iniciando suite de pruebas de JWT..."
echo ""

# Prueba 1: Autenticación básica
run_jwt_test "authentication_basic" 3 500

# Prueba 2: Flujo completo de JWT
run_jwt_test "jwt_complete_flow" 5 300

# Prueba 3: Pruebas de seguridad JWT
run_jwt_test "jwt_security_tests" 2 200

# Prueba 4: Pruebas de rendimiento JWT
run_jwt_test "jwt_performance" 10 100

# Prueba 5: Pruebas de roles y permisos
run_jwt_test "jwt_roles_permissions" 3 400

echo ""
echo "✅ Todas las pruebas de JWT han sido completadas"
echo "📁 Los resultados se han guardado en el directorio 'results/'"
echo ""

# Mostrar resumen de archivos generados
echo "📋 Archivos de resultados generados:"
ls -la results/poc3_jwt_*_$(date +%Y%m%d)*.json 2>/dev/null || echo "No se encontraron archivos de resultados"

echo ""
echo "🎯 Para ejecutar pruebas específicas:"
echo "   - Autenticación básica: newman run $COLLECTION_FILE --environment $ENVIRONMENT_FILE --iteration-count 3 --delay-request 500"
echo "   - Flujo completo: newman run $COLLECTION_FILE --environment $ENVIRONMENT_FILE --iteration-count 5 --delay-request 300"
echo "   - Pruebas de seguridad: newman run $COLLECTION_FILE --environment $ENVIRONMENT_FILE --iteration-count 2 --delay-request 200"
echo ""
echo "🔧 Para personalizar las pruebas, modifica las variables en este script:"
echo "   - ITERATIONS: Número de iteraciones por prueba"
echo "   - DELAY: Tiempo de espera entre requests"
echo ""
echo "📚 Documentación adicional:"
echo "   - Guía de JWT: POC3_JWT_DOCUMENTATION.md"
echo "   - Guía de pruebas: POC3_TESTING_GUIDE.md"
