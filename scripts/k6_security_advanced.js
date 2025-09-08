import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';

// Métricas personalizadas
const securityViolations = new Counter('security_violations');
const mfaBypassAttempts = new Counter('mfa_bypass_attempts');
const injectionAttempts = new Counter('injection_attempts');
const unauthorizedAccess = new Counter('unauthorized_access');

export const options = {
  stages: [
    { duration: '30s', target: 5 },  // Ramp up lento para pruebas de seguridad
    { duration: '2m', target: 10 },  // Mantener carga moderada
    { duration: '30s', target: 0 },  // Ramp down
  ],
  thresholds: {
    security_violations: ['count<10'], // Máximo 10 violaciones de seguridad
    mfa_bypass_attempts: ['count<5'],  // Máximo 5 intentos de bypass MFA
    injection_attempts: ['count<3'],   // Máximo 3 intentos de inyección
    unauthorized_access: ['count<5'],  // Máximo 5 accesos no autorizados
  },
};

const BASE_URL = 'http://localhost:8083';

// Payloads de prueba de seguridad
const securityPayloads = {
  // Intentos de bypass MFA
  mfaBypass: [
    { header: 'x-mfa', value: 'false' },
    { header: 'x-mfa', value: '1' },
    { header: 'x-mfa', value: 'yes' },
    { header: 'x-mfa', value: 'TRUE' },
    { header: 'x-mfa', value: 'true ' }, // Con espacio
    { header: 'x-mfa', value: 'true\x00' }, // Con null byte
  ],
  
  // Headers maliciosos
  maliciousHeaders: [
    { 'x-forwarded-for': '127.0.0.1' },
    { 'x-real-ip': '192.168.1.1' },
    { 'x-originating-ip': '10.0.0.1' },
    { 'x-remote-ip': '172.16.0.1' },
    { 'x-client-ip': '203.0.113.1' },
    { 'user-agent': 'Mozilla/5.0 (compatible; SecurityTest/1.0)' },
    { 'referer': 'https://malicious-site.com' },
    { 'origin': 'https://evil.com' },
  ],
  
  // Payloads de inyección
  injectionPayloads: [
    // SQL Injection (aunque no aplica directamente, es buena práctica probar)
    { name: "'; DROP TABLE customers; --", email: 'injection@test.com', phone: '+57-300' },
    { name: 'Test', email: "admin'--", phone: '+57-300' },
    { name: 'Test', email: 'test@test.com', phone: "'; SELECT * FROM users; --" },
    
    // XSS
    { name: '<script>alert("xss")</script>', email: 'xss@test.com', phone: '+57-300' },
    { name: 'Test', email: 'test@test.com', phone: '<img src=x onerror=alert(1)>' },
    
    // Command Injection
    { name: 'Test; rm -rf /', email: 'cmd@test.com', phone: '+57-300' },
    { name: 'Test', email: 'test@test.com', phone: '$(whoami)' },
    
    // Path Traversal
    { name: '../../../etc/passwd', email: 'path@test.com', phone: '+57-300' },
    { name: 'Test', email: 'test@test.com', phone: '..\\..\\windows\\system32\\drivers\\etc\\hosts' },
  ],
  
  // Datos con caracteres especiales problemáticos
  specialChars: [
    { name: 'Test\x00User', email: 'null@test.com', phone: '+57-300' },
    { name: 'Test\r\nUser', email: 'crlf@test.com', phone: '+57-300' },
    { name: 'Test\tUser', email: 'tab@test.com', phone: '+57-300' },
    { name: 'Test"User', email: 'quote@test.com', phone: '+57-300' },
    { name: "Test'User", email: 'apostrophe@test.com', phone: '+57-300' },
    { name: 'Test\\User', email: 'backslash@test.com', phone: '+57-300' },
    { name: 'Test/User', email: 'slash@test.com', phone: '+57-300' },
  ],
  
  // Datos extremadamente largos
  longData: [
    { name: 'A'.repeat(10000), email: 'longname@test.com', phone: '+57-300' },
    { name: 'Test', email: 'a'.repeat(1000) + '@test.com', phone: '+57-300' },
    { name: 'Test', email: 'test@test.com', phone: '+57-300-' + '1'.repeat(1000) },
  ],
  
  // Datos con encoding problemático
  encodingIssues: [
    { name: 'Test\xc0\x80User', email: 'overlong@test.com', phone: '+57-300' },
    { name: 'Test\xff\xfeUser', email: 'bom@test.com', phone: '+57-300' },
    { name: 'Test\xf0\x9f\x98\x80User', email: 'emoji@test.com', phone: '+57-300' },
  ]
};

// Función para probar bypass de MFA
function testMFABypass() {
  const customer = {
    name: 'MFA Bypass Test',
    email: `mfa-bypass-${Math.floor(Math.random() * 10000)}@test.com`,
    phone: '+57-300-0000'
  };
  
  securityPayloads.mfaBypass.forEach((payload, index) => {
    const headers = {
      'Content-Type': 'application/json',
      [payload.header]: payload.value
    };
    
    const response = http.post(`${BASE_URL}/customers`, JSON.stringify(customer), {
      headers: headers
    });
    
    const isUnauthorized = response.status === 401;
    const isAuthorized = response.status === 200;
    
    check(response, {
      [`MFA bypass attempt ${index + 1} properly rejected`]: (r) => isUnauthorized,
    });
    
    if (isAuthorized) {
      mfaBypassAttempts.add(1);
      console.log(`⚠️  MFA bypass successful with ${payload.header}: ${payload.value}`);
    }
    
    sleep(0.1);
  });
}

// Función para probar headers maliciosos
function testMaliciousHeaders() {
  const customer = {
    name: 'Header Test',
    email: `header-test-${Math.floor(Math.random() * 10000)}@test.com`,
    phone: '+57-300-1111'
  };
  
  securityPayloads.maliciousHeaders.forEach((headers, index) => {
    const requestHeaders = {
      'Content-Type': 'application/json',
      'x-mfa': 'true',
      ...headers
    };
    
    const response = http.post(`${BASE_URL}/customers`, JSON.stringify(customer), {
      headers: requestHeaders
    });
    
    check(response, {
      [`Malicious header ${index + 1} handled properly`]: (r) => r.status === 200,
    });
    
    sleep(0.1);
  });
}

// Función para probar inyección
function testInjection() {
  securityPayloads.injectionPayloads.forEach((payload, index) => {
    const headers = {
      'Content-Type': 'application/json',
      'x-mfa': 'true'
    };
    
    const response = http.post(`${BASE_URL}/customers`, JSON.stringify(payload), {
      headers: headers
    });
    
    const isRejected = response.status === 422 || response.status === 400;
    const isAccepted = response.status === 200;
    
    check(response, {
      [`Injection payload ${index + 1} properly handled`]: (r) => isRejected || isAccepted,
    });
    
    if (isAccepted) {
      injectionAttempts.add(1);
      console.log(`⚠️  Injection payload accepted: ${JSON.stringify(payload)}`);
    }
    
    sleep(0.1);
  });
}

// Función para probar caracteres especiales
function testSpecialCharacters() {
  securityPayloads.specialChars.forEach((payload, index) => {
    const headers = {
      'Content-Type': 'application/json',
      'x-mfa': 'true'
    };
    
    const response = http.post(`${BASE_URL}/customers`, JSON.stringify(payload), {
      headers: headers
    });
    
    check(response, {
      [`Special character test ${index + 1} handled`]: (r) => r.status === 200 || r.status === 422,
    });
    
    sleep(0.1);
  });
}

// Función para probar datos largos
function testLongData() {
  securityPayloads.longData.forEach((payload, index) => {
    const headers = {
      'Content-Type': 'application/json',
      'x-mfa': 'true'
    };
    
    const response = http.post(`${BASE_URL}/customers`, JSON.stringify(payload), {
      headers: headers
    });
    
    check(response, {
      [`Long data test ${index + 1} handled`]: (r) => r.status === 200 || r.status === 413 || r.status === 422,
    });
    
    sleep(0.1);
  });
}

// Función para probar acceso no autorizado
function testUnauthorizedAccess() {
  const testEmail = 'unauthorized-test@test.com';
  
  // Intentar acceso sin MFA
  const response1 = http.get(`${BASE_URL}/customers/${testEmail}`);
  check(response1, {
    'Unauthorized access properly rejected': (r) => r.status === 401,
  });
  
  if (response1.status !== 401) {
    unauthorizedAccess.add(1);
  }
  
  // Intentar acceso con MFA falso
  const response2 = http.get(`${BASE_URL}/customers/${testEmail}`, {
    headers: { 'x-mfa': 'false' }
  });
  check(response2, {
    'False MFA properly rejected': (r) => r.status === 401,
  });
  
  if (response2.status !== 401) {
    unauthorizedAccess.add(1);
  }
  
  sleep(0.1);
}

// Función para probar métodos HTTP no permitidos
function testUnsupportedMethods() {
  const customer = {
    name: 'Method Test',
    email: 'method-test@test.com',
    phone: '+57-300-2222'
  };
  
  const methods = ['PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'];
  
  methods.forEach(method => {
    const response = http.request(method, `${BASE_URL}/customers`, JSON.stringify(customer), {
      headers: { 'Content-Type': 'application/json', 'x-mfa': 'true' }
    });
    
    check(response, {
      [`${method} method properly rejected`]: (r) => r.status === 405 || r.status === 404,
    });
    
    sleep(0.1);
  });
}

// Función para probar Content-Type incorrecto
function testInvalidContentType() {
  const customer = {
    name: 'Content Type Test',
    email: 'content-type-test@test.com',
    phone: '+57-300-3333'
  };
  
  const contentTypes = [
    'text/plain',
    'application/x-www-form-urlencoded',
    'multipart/form-data',
    'text/html',
    'application/xml'
  ];
  
  contentTypes.forEach(contentType => {
    const response = http.post(`${BASE_URL}/customers`, JSON.stringify(customer), {
      headers: { 'Content-Type': contentType, 'x-mfa': 'true' }
    });
    
    check(response, {
      [`Invalid content type ${contentType} handled`]: (r) => r.status === 415 || r.status === 422 || r.status === 200,
    });
    
    sleep(0.1);
  });
}

export default function() {
  // Ejecutar diferentes tipos de pruebas de seguridad
  const testType = Math.floor(Math.random() * 7);
  
  switch (testType) {
    case 0:
      testMFABypass();
      break;
    case 1:
      testMaliciousHeaders();
      break;
    case 2:
      testInjection();
      break;
    case 3:
      testSpecialCharacters();
      break;
    case 4:
      testLongData();
      break;
    case 5:
      testUnauthorizedAccess();
      break;
    case 6:
      testUnsupportedMethods();
      break;
    default:
      testInvalidContentType();
  }
  
  sleep(1); // Pausa entre iteraciones
}

export function setup() {
  console.log('Iniciando pruebas de seguridad avanzadas...');
  return {};
}

export function teardown(data) {
  console.log('Finalizando pruebas de seguridad...');
  console.log(`Total violaciones de seguridad: ${securityViolations.count}`);
  console.log(`Intentos de bypass MFA: ${mfaBypassAttempts.count}`);
  console.log(`Intentos de inyección: ${injectionAttempts.count}`);
  console.log(`Accesos no autorizados: ${unauthorizedAccess.count}`);
}
