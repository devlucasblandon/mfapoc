#!/bin/bash

# Script para ejecutar pruebas de carga del POC3 con Newman
# Este script ejecuta la colección de Postman múltiples veces para simular carga

set -e

echo "🚀 Iniciando pruebas de carga del POC3 Security con Newman..."

# Verificar que Newman esté instalado
if ! command -v newman &> /dev/null; then
    echo "❌ Newman no está instalado. Instalando..."
    npm install -g newman
fi

# Verificar que el POC3 esté ejecutándose
echo "🔍 Verificando que POC3 esté ejecutándose..."
if ! curl -s http://localhost:8083/customers/nonexistent@test.com -H "x-mfa: true" > /dev/null; then
    echo "❌ POC3 no está ejecutándose en http://localhost:8083"
    echo "💡 Ejecuta 'make poc3' primero"
    exit 1
fi

echo "✅ POC3 está ejecutándose correctamente"

# Configuración de las pruebas
COLLECTION_FILE="postman/POC3_Security.postman_collection.json"
ENVIRONMENT_FILE="postman/environment.medisupply.local.json"
ITERATIONS=10
CONCURRENT_USERS=5

echo "📊 Configuración de las pruebas:"
echo "   - Colección: $COLLECTION_FILE"
echo "   - Entorno: $ENVIRONMENT_FILE"
echo "   - Iteraciones: $ITERATIONS"
echo "   - Usuarios concurrentes: $CONCURRENT_USERS"
echo ""

# Función para ejecutar pruebas con diferentes configuraciones
run_load_test() {
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
        --reporter-json-export "results/poc3_${test_name// /_}_$(date +%Y%m%d_%H%M%S).json" \
        --suppress-exit-code
}

# Crear directorio de resultados
mkdir -p results

echo "🏁 Iniciando suite de pruebas de carga..."
echo ""

# Prueba 1: Carga ligera
run_load_test "light_load" 5 1000

# Prueba 2: Carga media
run_load_test "medium_load" 10 500

# Prueba 3: Carga pesada
run_load_test "heavy_load" 20 200

# Prueba 4: Carga de pico (sin delay)
run_load_test "peak_load" 15 0

# Prueba 5: Carga sostenida
run_load_test "sustained_load" 25 300

echo ""
echo "✅ Todas las pruebas de carga han sido completadas"
echo "📁 Los resultados se han guardado en el directorio 'results/'"
echo ""

# Mostrar resumen de archivos generados
echo "📋 Archivos de resultados generados:"
ls -la results/poc3_*_$(date +%Y%m%d)*.json 2>/dev/null || echo "No se encontraron archivos de resultados"

echo ""
echo "🎯 Para ejecutar pruebas específicas:"
echo "   - Prueba ligera: newman run $COLLECTION_FILE --environment $ENVIRONMENT_FILE --iteration-count 5 --delay-request 1000"
echo "   - Prueba media: newman run $COLLECTION_FILE --environment $ENVIRONMENT_FILE --iteration-count 10 --delay-request 500"
echo "   - Prueba pesada: newman run $COLLECTION_FILE --environment $ENVIRONMENT_FILE --iteration-count 20 --delay-request 200"
echo ""
echo "🔧 Para personalizar las pruebas, modifica las variables en este script:"
echo "   - ITERATIONS: Número de iteraciones por prueba"
echo "   - CONCURRENT_USERS: Usuarios concurrentes (para futuras implementaciones)"
echo "   - DELAY: Tiempo de espera entre requests"
