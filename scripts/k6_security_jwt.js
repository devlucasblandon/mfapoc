import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Métricas personalizadas
const jwtAuthSuccess = new Rate('jwt_auth_success_rate');
const jwtValidationTime = new Trend('jwt_validation_time');
const tokenRefreshSuccess = new Rate('token_refresh_success_rate');
const unauthorizedAccess = new Counter('unauthorized_access_attempts');
const roleViolations = new Counter('role_violation_attempts');

export const options = {
  stages: [
    { duration: '30s', target: 5 },  // Ramp up
    { duration: '2m', target: 10 },  // Mantener carga
    { duration: '30s', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    jwt_auth_success_rate: ['rate>0.95'],
    jwt_validation_time: ['p(95)<100'],
    token_refresh_success_rate: ['rate>0.99'],
    unauthorized_access_attempts: ['count<5'],
    role_violation_attempts: ['count<3'],
  },
};

const BASE_URL = 'http://localhost:8083';

// Usuarios de prueba
const testUsers = [
  { username: 'admin', password: 'admin123', roles: ['admin', 'user'] },
  { username: 'user1', password: 'user123', roles: ['user'] },
  { username: 'user2', password: 'user123', roles: ['user'] }
];

// Función para hacer login y obtener token
function loginUser(username, password) {
  const loginPayload = JSON.stringify({
    username: username,
    password: password
  });
  
  const loginResponse = http.post(`${BASE_URL}/auth/login`, loginPayload, {
    headers: { 'Content-Type': 'application/json' }
  });
  
  const loginSuccess = check(loginResponse, {
    'login successful': (r) => r.status === 200,
    'login response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  jwtAuthSuccess.add(loginSuccess);
  
  if (loginSuccess) {
    const responseData = JSON.parse(loginResponse.body);
    return {
      access_token: responseData.access_token,
      refresh_token: responseData.refresh_token,
      token_type: responseData.token_type
    };
  }
  
  return null;
}

// Función para validar token
function validateToken(token) {
  const start = Date.now();
  
  const response = http.get(`${BASE_URL}/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const end = Date.now();
  jwtValidationTime.add(end - start);
  
  const success = check(response, {
    'token validation successful': (r) => r.status === 200,
    'token validation time < 100ms': (r) => r.timings.duration < 100,
  });
  
  return { response, success };
}

// Función para refrescar token
function refreshToken(refreshToken) {
  const refreshPayload = JSON.stringify({
    refresh_token: refreshToken
  });
  
  const response = http.post(`${BASE_URL}/auth/refresh`, refreshPayload, {
    headers: { 'Content-Type': 'application/json' }
  });
  
  const success = check(response, {
    'token refresh successful': (r) => r.status === 200,
    'token refresh time < 200ms': (r) => r.timings.duration < 200,
  });
  
  tokenRefreshSuccess.add(success);
  
  if (success) {
    const responseData = JSON.parse(response.body);
    return responseData.access_token;
  }
  
  return null;
}

// Función para crear cliente con JWT
function createCustomerWithJWT(token, customerData) {
  const response = http.post(`${BASE_URL}/customers`, JSON.stringify(customerData), {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  });
  
  const success = check(response, {
    'customer creation successful': (r) => r.status === 200,
    'customer creation time < 300ms': (r) => r.timings.duration < 300,
  });
  
  return { response, success };
}

// Función para obtener cliente con JWT
function getCustomerWithJWT(token, email) {
  const response = http.get(`${BASE_URL}/customers/${email}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const success = check(response, {
    'customer retrieval successful': (r) => r.status === 200,
    'customer retrieval time < 200ms': (r) => r.timings.duration < 200,
  });
  
  return { response, success };
}

// Función para probar acceso sin token
function testUnauthorizedAccess() {
  const response = http.get(`${BASE_URL}/auth/me`);
  
  const isUnauthorized = response.status === 401;
  check(response, {
    'unauthorized access properly rejected': (r) => isUnauthorized,
  });
  
  if (!isUnauthorized) {
    unauthorizedAccess.add(1);
  }
  
  return isUnauthorized;
}

// Función para probar token inválido
function testInvalidToken() {
  const invalidTokens = [
    'invalid-token',
    'Bearer invalid-token',
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid',
    'expired-token'
  ];
  
  invalidTokens.forEach(token => {
    const response = http.get(`${BASE_URL}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const isUnauthorized = response.status === 401;
    check(response, {
      'invalid token properly rejected': (r) => isUnauthorized,
    });
    
    if (!isUnauthorized) {
      unauthorizedAccess.add(1);
    }
  });
}

// Función para probar violación de roles
function testRoleViolation(userToken, adminOnlyEndpoint) {
  const response = http.request('DELETE', `${BASE_URL}/customers/test@example.com`, null, {
    headers: { 'Authorization': `Bearer ${userToken}` }
  });
  
  const isForbidden = response.status === 403;
  check(response, {
    'role violation properly rejected': (r) => isForbidden,
  });
  
  if (!isForbidden) {
    roleViolations.add(1);
  }
  
  return isForbidden;
}

// Función para probar flujo completo de autenticación
function testCompleteAuthFlow() {
  const user = testUsers[Math.floor(Math.random() * testUsers.length)];
  
  // 1. Login
  const tokens = loginUser(user.username, user.password);
  if (!tokens) {
    return false;
  }
  
  // 2. Validar token
  const validation = validateToken(tokens.access_token);
  if (!validation.success) {
    return false;
  }
  
  // 3. Crear cliente
  const customerData = {
    name: `Test User ${Math.floor(Math.random() * 10000)}`,
    email: `test${Math.floor(Math.random() * 10000)}@example.com`,
    phone: `+57-300-${Math.floor(Math.random() * 10000)}`
  };
  
  const creation = createCustomerWithJWT(tokens.access_token, customerData);
  if (!creation.success) {
    return false;
  }
  
  // 4. Obtener cliente
  const retrieval = getCustomerWithJWT(tokens.access_token, customerData.email);
  if (!retrieval.success) {
    return false;
  }
  
  // 5. Refrescar token
  const newToken = refreshToken(tokens.refresh_token);
  if (!newToken) {
    return false;
  }
  
  // 6. Validar nuevo token
  const newValidation = validateToken(newToken);
  if (!newValidation.success) {
    return false;
  }
  
  return true;
}

export default function() {
  const testType = Math.floor(Math.random() * 6);
  
  switch (testType) {
    case 0:
      // Flujo completo de autenticación
      testCompleteAuthFlow();
      break;
      
    case 1:
      // Pruebas de acceso no autorizado
      testUnauthorizedAccess();
      break;
      
    case 2:
      // Pruebas de token inválido
      testInvalidToken();
      break;
      
    case 3:
      // Pruebas de violación de roles
      const userTokens = loginUser('user1', 'user123');
      if (userTokens) {
        testRoleViolation(userTokens.access_token, '/customers/test@example.com');
      }
      break;
      
    case 4:
      // Pruebas de rendimiento de login
      const randomUser = testUsers[Math.floor(Math.random() * testUsers.length)];
      loginUser(randomUser.username, randomUser.password);
      break;
      
    case 5:
      // Pruebas de validación de token
      const tokens = loginUser('admin', 'admin123');
      if (tokens) {
        validateToken(tokens.access_token);
      }
      break;
  }
  
  sleep(0.5);
}

export function setup() {
  console.log('Iniciando pruebas de JWT para POC3 Security...');
  
  // Verificar que el servicio esté ejecutándose
  const healthCheck = http.get(`${BASE_URL}/auth/demo-tokens`);
  if (healthCheck.status !== 200) {
    console.log('❌ POC3 no está ejecutándose correctamente');
    return {};
  }
  
  console.log('✅ POC3 está ejecutándose correctamente');
  
  // Obtener tokens de demostración
  const demoResponse = http.get(`${BASE_URL}/auth/demo-tokens`);
  if (demoResponse.status === 200) {
    const demoData = JSON.parse(demoResponse.body);
    console.log('✅ Tokens de demostración obtenidos');
    return { demoTokens: demoData };
  }
  
  return {};
}

export function teardown(data) {
  console.log('Finalizando pruebas de JWT...');
  console.log(`Tasa de éxito de autenticación: ${(jwtAuthSuccess.count / jwtAuthSuccess.total * 100).toFixed(2)}%`);
  console.log(`Tiempo promedio de validación JWT: ${jwtValidationTime.avg.toFixed(2)}ms`);
  console.log(`Tasa de éxito de refresh token: ${(tokenRefreshSuccess.count / tokenRefreshSuccess.total * 100).toFixed(2)}%`);
  console.log(`Intentos de acceso no autorizado: ${unauthorizedAccess.count}`);
  console.log(`Intentos de violación de roles: ${roleViolations.count}`);
}
