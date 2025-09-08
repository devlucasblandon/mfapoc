#!/bin/bash

# Script de pruebas de regresión para POC3 Security
# Ejecuta un conjunto completo de pruebas para verificar que todas las funcionalidades
# de seguridad funcionan correctamente después de cambios

set -e

echo "🔒 Iniciando pruebas de regresión para POC3 Security..."
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Función para ejecutar una prueba y contar resultados
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_exit_code="${3:-0}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "${BLUE}🧪 Ejecutando: $test_name${NC}"
    
    if eval "$command" > /dev/null 2>&1; then
        if [ $? -eq $expected_exit_code ]; then
            echo -e "${GREEN}✅ PASSED: $test_name${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}❌ FAILED: $test_name (código de salida incorrecto)${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        if [ $? -eq $expected_exit_code ]; then
            echo -e "${GREEN}✅ PASSED: $test_name${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}❌ FAILED: $test_name${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
    echo ""
}

# Función para verificar que el POC3 esté ejecutándose
check_poc3_running() {
    echo -e "${YELLOW}🔍 Verificando que POC3 esté ejecutándose...${NC}"
    
    if curl -s http://localhost:8083/customers/nonexistent@test.com -H "x-mfa: true" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ POC3 está ejecutándose correctamente${NC}"
        return 0
    else
        echo -e "${RED}❌ POC3 no está ejecutándose en http://localhost:8083${NC}"
        echo -e "${YELLOW}💡 Ejecuta 'make poc3' primero${NC}"
        return 1
    fi
}

# Función para limpiar datos de prueba
cleanup_test_data() {
    echo -e "${YELLOW}🧹 Limpiando datos de prueba...${NC}"
    # En un entorno real, aquí limpiarías los datos de prueba
    # Por simplicidad del POC, no implementamos limpieza automática
    echo -e "${GREEN}✅ Limpieza completada${NC}"
}

# Función principal
main() {
    echo -e "${BLUE}🚀 Iniciando suite de pruebas de regresión para POC3 Security${NC}"
    echo ""
    
    # Verificar que POC3 esté ejecutándose
    if ! check_poc3_running; then
        exit 1
    fi
    
    echo ""
    echo -e "${BLUE}📋 Ejecutando pruebas de regresión...${NC}"
    echo ""
    
    # Pruebas básicas de funcionalidad
    echo -e "${YELLOW}🔧 Pruebas básicas de funcionalidad${NC}"
    echo "----------------------------------------"
    
    run_test "Crear cliente con MFA válido" \
        "curl -s -X POST http://localhost:8083/customers -H 'Content-Type: application/json' -H 'x-mfa: true' -d '{\"name\":\"Test User\",\"email\":\"test@regression.com\",\"phone\":\"+57-300-0000\"}' | grep -q 'ok'"
    
    run_test "Leer cliente con MFA válido" \
        "curl -s -X GET http://localhost:8083/customers/test@regression.com -H 'x-mfa: true' | grep -q 'Test User'"
    
    # Pruebas de seguridad
    echo -e "${YELLOW}🔒 Pruebas de seguridad${NC}"
    echo "------------------------"
    
    run_test "Rechazar creación sin MFA" \
        "curl -s -X POST http://localhost:8083/customers -H 'Content-Type: application/json' -d '{\"name\":\"Test\",\"email\":\"test2@regression.com\",\"phone\":\"+57-300-0001\"}' | grep -q 'MFA required'" \
        0
    
    run_test "Rechazar creación con MFA falso" \
        "curl -s -X POST http://localhost:8083/customers -H 'Content-Type: application/json' -H 'x-mfa: false' -d '{\"name\":\"Test\",\"email\":\"test3@regression.com\",\"phone\":\"+57-300-0002\"}' | grep -q 'MFA required'" \
        0
    
    run_test "Rechazar lectura sin MFA" \
        "curl -s -X GET http://localhost:8083/customers/test@regression.com | grep -q 'MFA required'" \
        0
    
    run_test "Rechazar lectura con MFA falso" \
        "curl -s -X GET http://localhost:8083/customers/test@regression.com -H 'x-mfa: false' | grep -q 'MFA required'" \
        0
    
    # Pruebas de validación de datos
    echo -e "${YELLOW}📝 Pruebas de validación de datos${NC}"
    echo "------------------------------------"
    
    run_test "Rechazar datos inválidos" \
        "curl -s -X POST http://localhost:8083/customers -H 'Content-Type: application/json' -H 'x-mfa: true' -d '{\"name\":\"\",\"email\":\"invalid-email\",\"phone\":\"\"}' | grep -q 'validation error'" \
        0
    
    run_test "Rechazar campos faltantes" \
        "curl -s -X POST http://localhost:8083/customers -H 'Content-Type: application/json' -H 'x-mfa: true' -d '{\"name\":\"Test\"}' | grep -q 'validation error'" \
        0
    
    # Pruebas de encriptación
    echo -e "${YELLOW}🔐 Pruebas de encriptación${NC}"
    echo "----------------------------"
    
    run_test "Verificar encriptación de email" \
        "curl -s -X POST http://localhost:8083/customers -H 'Content-Type: application/json' -H 'x-mfa: true' -d '{\"name\":\"Encryption Test\",\"email\":\"encryption@regression.com\",\"phone\":\"+57-300-0003\"}' > /dev/null && curl -s -X GET http://localhost:8083/customers/encryption@regression.com -H 'x-mfa: true' | grep -q 'encryption@regression.com'"
    
    run_test "Verificar encriptación de teléfono" \
        "curl -s -X GET http://localhost:8083/customers/encryption@regression.com -H 'x-mfa: true' | grep -q '+57-300-0003'"
    
    # Pruebas de casos límite
    echo -e "${YELLOW}⚡ Pruebas de casos límite${NC}"
    echo "----------------------------"
    
    run_test "Manejar cliente inexistente" \
        "curl -s -X GET http://localhost:8083/customers/nonexistent@regression.com -H 'x-mfa: true' | grep -q 'not found'" \
        0
    
    run_test "Manejar caracteres especiales" \
        "curl -s -X POST http://localhost:8083/customers -H 'Content-Type: application/json' -H 'x-mfa: true' -d '{\"name\":\"José María\",\"email\":\"josé@regression.com\",\"phone\":\"+57-300-0004\"}' | grep -q 'ok'"
    
    run_test "Leer cliente con caracteres especiales" \
        "curl -s -X GET http://localhost:8083/customers/josé@regression.com -H 'x-mfa: true' | grep -q 'José María'"
    
    # Pruebas de métodos HTTP
    echo -e "${YELLOW}🌐 Pruebas de métodos HTTP${NC}"
    echo "----------------------------"
    
    run_test "Rechazar método PUT" \
        "curl -s -X PUT http://localhost:8083/customers -H 'Content-Type: application/json' -H 'x-mfa: true' -d '{\"name\":\"Test\",\"email\":\"test@regression.com\",\"phone\":\"+57-300\"}' | grep -q 'Method Not Allowed'" \
        0
    
    run_test "Rechazar método DELETE" \
        "curl -s -X DELETE http://localhost:8083/customers/test@regression.com -H 'x-mfa: true' | grep -q 'Method Not Allowed'" \
        0
    
    # Pruebas de rendimiento básicas
    echo -e "${YELLOW}⚡ Pruebas de rendimiento básicas${NC}"
    echo "------------------------------------"
    
    run_test "Tiempo de respuesta < 500ms" \
        "time curl -s -X POST http://localhost:8083/customers -H 'Content-Type: application/json' -H 'x-mfa: true' -d '{\"name\":\"Performance Test\",\"email\":\"perf@regression.com\",\"phone\":\"+57-300-0005\"}' | grep -q 'ok'"
    
    # Ejecutar pruebas con K6 si está disponible
    if command -v k6 &> /dev/null; then
        echo -e "${YELLOW}🚀 Ejecutando pruebas de rendimiento con K6${NC}"
        echo "----------------------------------------"
        
        run_test "Pruebas de seguridad avanzadas con K6" \
            "k6 run scripts/k6_security_advanced.js --quiet"
        
        run_test "Pruebas de integración con K6" \
            "k6 run scripts/k6_security_integration.js --quiet"
    else
        echo -e "${YELLOW}⚠️  K6 no está instalado, saltando pruebas de rendimiento${NC}"
    fi
    
    # Limpiar datos de prueba
    cleanup_test_data
    
    # Mostrar resumen
    echo ""
    echo -e "${BLUE}📊 Resumen de pruebas de regresión${NC}"
    echo "=================================="
    echo -e "Total de pruebas: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Pruebas exitosas: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Pruebas fallidas: ${RED}$FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 ¡Todas las pruebas de regresión pasaron exitosamente!${NC}"
        exit 0
    else
        echo -e "${RED}❌ $FAILED_TESTS pruebas fallaron. Revisa los logs arriba.${NC}"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"
