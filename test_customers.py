#!/usr/bin/env python3
"""
Script para probar el endpoint /customers (POST) del POC 3
"""

import requests
import json
import time
import sys

# Configuración
BASE_URL = "http://localhost:8087"
API_URL = f"{BASE_URL}/api/v1"

def test_health():
    """Probar health check"""
    print("🔍 Probando health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check OK")
            return True
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_login():
    """Probar login y obtener token"""
    print("🔐 Probando login...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_URL}/auth/login", json=login_data, timeout=5)
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login exitoso")
            print(f"   Token: {token_data['access_token'][:50]}...")
            return token_data['access_token']
        else:
            print(f"❌ Login falló: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None

def test_create_customer(token):
    """Probar creación de cliente"""
    print("👥 Probando creación de cliente...")
    try:
        customer_data = {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "phone": "+57-300-123-4567"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{API_URL}/customers", json=customer_data, headers=headers, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Cliente creado exitosamente")
            print(f"   Respuesta: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Creación de cliente falló: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_list_customers(token):
    """Probar listado de clientes"""
    print("📋 Probando listado de clientes...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{API_URL}/customers", headers=headers, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Listado de clientes exitoso")
            print(f"   Total clientes: {result['total']}")
            for customer in result['customers']:
                print(f"   - {customer['name']} ({customer['email']})")
            return True
        else:
            print(f"❌ Listado de clientes falló: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_get_customer(token, email):
    """Probar obtención de cliente específico"""
    print(f"🔍 Probando obtención de cliente: {email}")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{API_URL}/customers/{email}", headers=headers, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Cliente obtenido exitosamente")
            print(f"   Nombre: {result['name']}")
            print(f"   Email: {result['email']}")
            print(f"   Teléfono: {result['phone']}")
            print(f"   Creado por: {result['created_by']}")
            return True
        else:
            print(f"❌ Obtención de cliente falló: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas del endpoint /customers (POST)")
    print("=" * 60)
    
    # Paso 1: Health check
    if not test_health():
        print("\n❌ No se puede conectar al servidor. Asegúrate de que esté ejecutándose.")
        sys.exit(1)
    
    # Paso 2: Login
    token = test_login()
    if not token:
        print("\n❌ No se pudo obtener token de autenticación.")
        sys.exit(1)
    
    # Paso 3: Crear cliente
    if not test_create_customer(token):
        print("\n❌ No se pudo crear el cliente.")
        sys.exit(1)
    
    # Paso 4: Listar clientes
    if not test_list_customers(token):
        print("\n❌ No se pudo listar los clientes.")
        sys.exit(1)
    
    # Paso 5: Obtener cliente específico
    if not test_get_customer(token, "alice@example.com"):
        print("\n❌ No se pudo obtener el cliente específico.")
        sys.exit(1)
    
    print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
    print("=" * 60)
    print("✅ Health check: OK")
    print("✅ Login: OK")
    print("✅ Crear cliente: OK")
    print("✅ Listar clientes: OK")
    print("✅ Obtener cliente: OK")

if __name__ == "__main__":
    main()
