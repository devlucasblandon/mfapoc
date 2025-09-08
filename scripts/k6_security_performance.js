import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Métricas personalizadas
const encryptionRate = new Rate('encryption_success_rate');
const encryptionTime = new Trend('encryption_time');
const decryptionTime = new Trend('decryption_time');
const mfaValidationTime = new Trend('mfa_validation_time');

export const options = {
  stages: [
    { duration: '30s', target: 10 }, // Ramp up
    { duration: '1m', target: 20 },  // Stay at 20 users
    { duration: '30s', target: 50 }, // Spike to 50 users
    { duration: '1m', target: 50 },  // Stay at 50 users
    { duration: '30s', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% de las requests deben ser < 500ms
    encryption_success_rate: ['rate>0.99'], // 99% de éxito en encriptación
    encryption_time: ['p(95)<100'], // 95% de encriptaciones < 100ms
    decryption_time: ['p(95)<100'], // 95% de desencriptaciones < 100ms
    mfa_validation_time: ['p(95)<50'], // 95% de validaciones MFA < 50ms
  },
};

const BASE_URL = 'http://localhost:8083';
const MFA_HEADER = { 'x-mfa': 'true' };

// Datos de prueba variados
const testCustomers = [
  {
    name: 'Performance Test User 1',
    email: 'perf1@test.com',
    phone: '+57-300-111-1111'
  },
  {
    name: 'Performance Test User 2',
    email: 'perf2@test.com',
    phone: '+57-300-222-2222'
  },
  {
    name: 'Performance Test User 3',
    email: 'perf3@test.com',
    phone: '+57-300-333-3333'
  },
  {
    name: 'Performance Test User 4',
    email: 'perf4@test.com',
    phone: '+57-300-444-4444'
  },
  {
    name: 'Performance Test User 5',
    email: 'perf5@test.com',
    phone: '+57-300-555-5555'
  }
];

// Función para generar datos aleatorios
function generateRandomCustomer() {
  const randomId = Math.floor(Math.random() * 10000);
  return {
    name: `Random User ${randomId}`,
    email: `random${randomId}@test.com`,
    phone: `+57-300-${String(randomId).padStart(4, '0')}`
  };
}

// Función para medir tiempo de encriptación
function measureEncryptionTime(customer) {
  const start = Date.now();
  const response = http.post(`${BASE_URL}/customers`, JSON.stringify(customer), {
    headers: { 'Content-Type': 'application/json', ...MFA_HEADER }
  });
  const end = Date.now();
  
  const success = check(response, {
    'encryption successful': (r) => r.status === 200,
    'encryption response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  encryptionRate.add(success);
  encryptionTime.add(end - start);
  
  return { response, success };
}

// Función para medir tiempo de desencriptación
function measureDecryptionTime(email) {
  const start = Date.now();
  const response = http.get(`${BASE_URL}/customers/${email}`, {
    headers: MFA_HEADER
  });
  const end = Date.now();
  
  const success = check(response, {
    'decryption successful': (r) => r.status === 200,
    'decryption response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  decryptionTime.add(end - start);
  
  return { response, success };
}

// Función para medir validación MFA
function measureMFAValidation() {
  const start = Date.now();
  const response = http.get(`${BASE_URL}/customers/nonexistent@test.com`, {
    headers: MFA_HEADER
  });
  const end = Date.now();
  
  mfaValidationTime.add(end - start);
  
  return response;
}

export default function() {
  // Escenario 1: Crear cliente con encriptación
  const customer = generateRandomCustomer();
  const { response: createResponse, success: createSuccess } = measureEncryptionTime(customer);
  
  if (createSuccess) {
    // Escenario 2: Leer cliente con desencriptación
    measureDecryptionTime(customer.email);
    
    // Escenario 3: Actualizar cliente (sobrescribir)
    const updatedCustomer = {
      ...customer,
      name: `${customer.name} Updated`,
      phone: `+57-300-${Math.floor(Math.random() * 10000)}`
    };
    measureEncryptionTime(updatedCustomer);
  }
  
  // Escenario 4: Validación MFA (cliente inexistente)
  measureMFAValidation();
  
  // Escenario 5: Prueba de carga con datos grandes
  if (Math.random() < 0.3) { // 30% de probabilidad
    const largeCustomer = {
      name: 'A'.repeat(100), // Nombre muy largo
      email: `large${Math.floor(Math.random() * 10000)}@verylongdomainname.com`,
      phone: '+57-300-' + '1'.repeat(20) // Teléfono muy largo
    };
    measureEncryptionTime(largeCustomer);
  }
  
  // Escenario 6: Prueba de caracteres especiales
  if (Math.random() < 0.2) { // 20% de probabilidad
    const specialCustomer = {
      name: 'José María González-López',
      email: `josé.maría+${Math.floor(Math.random() * 1000)}@example.com`,
      phone: '+57-300-123-4567'
    };
    measureEncryptionTime(specialCustomer);
  }
  
  // Escenario 7: Prueba de concurrencia (múltiples operaciones)
  if (Math.random() < 0.1) { // 10% de probabilidad
    const concurrentCustomers = testCustomers.slice(0, 3);
    concurrentCustomers.forEach(customer => {
      measureEncryptionTime(customer);
    });
  }
  
  sleep(0.1); // Pequeña pausa entre requests
}

// Función de setup para datos iniciales
export function setup() {
  console.log('Configurando datos iniciales para pruebas de rendimiento...');
  
  // Crear algunos clientes de prueba iniciales
  const initialCustomers = testCustomers.slice(0, 2);
  initialCustomers.forEach(customer => {
    const response = http.post(`${BASE_URL}/customers`, JSON.stringify(customer), {
      headers: { 'Content-Type': 'application/json', ...MFA_HEADER }
    });
    
    if (response.status !== 200) {
      console.log(`Error creando cliente inicial ${customer.email}: ${response.status}`);
    }
  });
  
  return { initialCustomers };
}

// Función de teardown para limpieza
export function teardown(data) {
  console.log('Limpiando datos de prueba...');
  // Nota: En un entorno real, aquí limpiarías los datos de prueba
  // Por simplicidad del POC, no implementamos limpieza automática
}
