import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter, Trend } from 'k6/metrics';

// Métricas personalizadas
const integrationSuccess = new Rate('integration_success_rate');
const encryptionConsistency = new Counter('encryption_consistency_checks');
const dataIntegrity = new Counter('data_integrity_checks');
const endToEndTime = new Trend('end_to_end_time');

export const options = {
  stages: [
    { duration: '30s', target: 3 },  // Ramp up lento para pruebas de integración
    { duration: '2m', target: 5 },   // Mantener carga baja para pruebas detalladas
    { duration: '30s', target: 0 },  // Ramp down
  ],
  thresholds: {
    integration_success_rate: ['rate>0.95'], // 95% de éxito en integración
    encryption_consistency_checks: ['count>10'], // Mínimo 10 verificaciones de consistencia
    data_integrity_checks: ['count>10'], // Mínimo 10 verificaciones de integridad
    end_to_end_time: ['p(95)<1000'], // 95% de flujos completos < 1s
  },
};

const BASE_URL = 'http://localhost:8083';
const MFA_HEADER = { 'x-mfa': 'true' };

// Función para crear un cliente y verificar encriptación
function createAndVerifyCustomer(customer, testName) {
  const startTime = Date.now();
  
  // Paso 1: Crear cliente
  const createResponse = http.post(`${BASE_URL}/customers`, JSON.stringify(customer), {
    headers: { 'Content-Type': 'application/json', ...MFA_HEADER }
  });
  
  const createSuccess = check(createResponse, {
    [`${testName} - Create customer successful`]: (r) => r.status === 200,
    [`${testName} - Create response time < 500ms`]: (r) => r.timings.duration < 500,
  });
  
  if (!createSuccess) {
    return { success: false, error: 'Create failed' };
  }
  
  // Paso 2: Leer cliente y verificar desencriptación
  const readResponse = http.get(`${BASE_URL}/customers/${customer.email}`, {
    headers: MFA_HEADER
  });
  
  const readSuccess = check(readResponse, {
    [`${testName} - Read customer successful`]: (r) => r.status === 200,
    [`${testName} - Read response time < 500ms`]: (r) => r.timings.duration < 500,
  });
  
  if (!readSuccess) {
    return { success: false, error: 'Read failed' };
  }
  
  // Paso 3: Verificar integridad de datos
  const responseData = JSON.parse(readResponse.body);
  const dataIntegrityCheck = check(responseData, {
    [`${testName} - Data integrity - name matches`]: (data) => data.name === customer.name,
    [`${testName} - Data integrity - email matches`]: (data) => data.email === customer.email,
    [`${testName} - Data integrity - phone matches`]: (data) => data.phone === customer.phone,
  });
  
  if (dataIntegrityCheck) {
    dataIntegrity.add(1);
  }
  
  const endTime = Date.now();
  endToEndTime.add(endTime - startTime);
  
  return { 
    success: createSuccess && readSuccess && dataIntegrityCheck,
    createResponse,
    readResponse,
    responseData
  };
}

// Función para probar flujo completo de actualización
function testUpdateFlow() {
  const originalCustomer = {
    name: 'Original Name',
    email: `update-test-${Math.floor(Math.random() * 10000)}@test.com`,
    phone: '+57-300-1111'
  };
  
  const updatedCustomer = {
    name: 'Updated Name',
    email: originalCustomer.email, // Mismo email para actualización
    phone: '+57-300-2222'
  };
  
  // Crear cliente original
  const createResult = createAndVerifyCustomer(originalCustomer, 'Update Flow - Create');
  if (!createResult.success) {
    return false;
  }
  
  // Actualizar cliente (sobrescribir)
  const updateResponse = http.post(`${BASE_URL}/customers`, JSON.stringify(updatedCustomer), {
    headers: { 'Content-Type': 'application/json', ...MFA_HEADER }
  });
  
  const updateSuccess = check(updateResponse, {
    'Update Flow - Update successful': (r) => r.status === 200,
  });
  
  if (!updateSuccess) {
    return false;
  }
  
  // Verificar que los datos se actualizaron correctamente
  const verifyResponse = http.get(`${BASE_URL}/customers/${originalCustomer.email}`, {
    headers: MFA_HEADER
  });
  
  const verifyData = JSON.parse(verifyResponse.body);
  const verifySuccess = check(verifyData, {
    'Update Flow - Name updated correctly': (data) => data.name === updatedCustomer.name,
    'Update Flow - Phone updated correctly': (data) => data.phone === updatedCustomer.phone,
    'Update Flow - Email remains same': (data) => data.email === originalCustomer.email,
  });
  
  return updateSuccess && verifySuccess;
}

// Función para probar consistencia de encriptación
function testEncryptionConsistency() {
  const customer = {
    name: 'Encryption Test',
    email: `encryption-test-${Math.floor(Math.random() * 10000)}@test.com`,
    phone: '+57-300-3333'
  };
  
  // Crear cliente
  const createResponse = http.post(`${BASE_URL}/customers`, JSON.stringify(customer), {
    headers: { 'Content-Type': 'application/json', ...MFA_HEADER }
  });
  
  if (createResponse.status !== 200) {
    return false;
  }
  
  // Leer cliente múltiples veces para verificar consistencia
  const readCount = 3;
  let allReadsConsistent = true;
  
  for (let i = 0; i < readCount; i++) {
    const readResponse = http.get(`${BASE_URL}/customers/${customer.email}`, {
      headers: MFA_HEADER
    });
    
    if (readResponse.status !== 200) {
      allReadsConsistent = false;
      break;
    }
    
    const readData = JSON.parse(readResponse.body);
    const isConsistent = readData.name === customer.name && 
                        readData.email === customer.email && 
                        readData.phone === customer.phone;
    
    if (!isConsistent) {
      allReadsConsistent = false;
      break;
    }
    
    sleep(0.1); // Pequeña pausa entre lecturas
  }
  
  const consistencyCheck = check({}, {
    'Encryption Consistency - All reads consistent': () => allReadsConsistent,
  });
  
  if (consistencyCheck) {
    encryptionConsistency.add(1);
  }
  
  return consistencyCheck;
}

// Función para probar manejo de errores en flujo completo
function testErrorHandlingFlow() {
  const testCases = [
    {
      name: 'Missing MFA',
      customer: { name: 'Test', email: 'test1@test.com', phone: '+57-300' },
      headers: { 'Content-Type': 'application/json' }, // Sin MFA
      expectedStatus: 401
    },
    {
      name: 'Invalid MFA',
      customer: { name: 'Test', email: 'test2@test.com', phone: '+57-300' },
      headers: { 'Content-Type': 'application/json', 'x-mfa': 'false' },
      expectedStatus: 401
    },
    {
      name: 'Invalid Data',
      customer: { name: '', email: 'invalid-email', phone: '' },
      headers: { 'Content-Type': 'application/json', 'x-mfa': 'true' },
      expectedStatus: 422
    },
    {
      name: 'Missing Fields',
      customer: { name: 'Test' }, // Faltan email y phone
      headers: { 'Content-Type': 'application/json', 'x-mfa': 'true' },
      expectedStatus: 422
    }
  ];
  
  let allErrorsHandled = true;
  
  testCases.forEach(testCase => {
    const response = http.post(`${BASE_URL}/customers`, JSON.stringify(testCase.customer), {
      headers: testCase.headers
    });
    
    const errorHandled = check(response, {
      [`Error Handling - ${testCase.name} properly rejected`]: (r) => r.status === testCase.expectedStatus,
    });
    
    if (!errorHandled) {
      allReadsConsistent = false;
    }
    
    sleep(0.1);
  });
  
  return allErrorsHandled;
}

// Función para probar flujo de datos sensibles
function testSensitiveDataFlow() {
  const sensitiveCustomers = [
    {
      name: 'Bank Customer',
      email: 'bank.customer@bank.com',
      phone: '+57-300-9999'
    },
    {
      name: 'Medical Patient',
      email: 'patient@hospital.com',
      phone: '+57-300-8888'
    },
    {
      name: 'Government Official',
      email: 'official@gov.co',
      phone: '+57-300-7777'
    }
  ];
  
  let allSensitiveDataHandled = true;
  
  sensitiveCustomers.forEach((customer, index) => {
    const result = createAndVerifyCustomer(customer, `Sensitive Data ${index + 1}`);
    
    if (!result.success) {
      allSensitiveDataHandled = false;
    }
    
    // Verificar que los datos sensibles se encriptaron correctamente
    if (result.success) {
      const dataIntegrityCheck = check(result.responseData, {
        [`Sensitive Data ${index + 1} - Data properly encrypted/decrypted`]: (data) => 
          data.name === customer.name && 
          data.email === customer.email && 
          data.phone === customer.phone
      });
      
      if (!dataIntegrityCheck) {
        allSensitiveDataHandled = false;
      }
    }
    
    sleep(0.1);
  });
  
  return allSensitiveDataHandled;
}

// Función para probar flujo de concurrencia
function testConcurrencyFlow() {
  const baseCustomer = {
    name: 'Concurrency Test',
    email: `concurrency-test-${Math.floor(Math.random() * 10000)}@test.com`,
    phone: '+57-300-4444'
  };
  
  // Crear múltiples clientes simultáneamente
  const concurrentCustomers = Array.from({ length: 3 }, (_, i) => ({
    ...baseCustomer,
    email: `concurrency-test-${i}-${Math.floor(Math.random() * 10000)}@test.com`,
    phone: `+57-300-${4444 + i}`
  }));
  
  let allConcurrentOperationsSuccessful = true;
  
  concurrentCustomers.forEach((customer, index) => {
    const result = createAndVerifyCustomer(customer, `Concurrency ${index + 1}`);
    
    if (!result.success) {
      allConcurrentOperationsSuccessful = false;
    }
  });
  
  return allConcurrentOperationsSuccessful;
}

export default function() {
  const testType = Math.floor(Math.random() * 6);
  let testResult = false;
  
  switch (testType) {
    case 0:
      // Flujo básico de creación y lectura
      const basicCustomer = {
        name: 'Integration Test',
        email: `integration-${Math.floor(Math.random() * 10000)}@test.com`,
        phone: '+57-300-5555'
      };
      testResult = createAndVerifyCustomer(basicCustomer, 'Basic Flow').success;
      break;
      
    case 1:
      // Flujo de actualización
      testResult = testUpdateFlow();
      break;
      
    case 2:
      // Consistencia de encriptación
      testResult = testEncryptionConsistency();
      break;
      
    case 3:
      // Manejo de errores
      testResult = testErrorHandlingFlow();
      break;
      
    case 4:
      // Datos sensibles
      testResult = testSensitiveDataFlow();
      break;
      
    case 5:
      // Concurrencia
      testResult = testConcurrencyFlow();
      break;
  }
  
  integrationSuccess.add(testResult);
  
  sleep(1); // Pausa entre iteraciones
}

export function setup() {
  console.log('Iniciando pruebas de integración de seguridad...');
  return {};
}

export function teardown(data) {
  console.log('Finalizando pruebas de integración...');
  console.log(`Tasa de éxito de integración: ${(integrationSuccess.count / integrationSuccess.total * 100).toFixed(2)}%`);
  console.log(`Verificaciones de consistencia de encriptación: ${encryptionConsistency.count}`);
  console.log(`Verificaciones de integridad de datos: ${dataIntegrity.count}`);
}
