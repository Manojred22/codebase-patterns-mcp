/**
 * Acme HTTP Client — standard wrapper for all outgoing HTTP calls.
 * Injects X-Acme-Service and X-Acme-Request-ID headers automatically.
 * Includes retry with exponential backoff.
 *
 * All outgoing HTTP calls MUST use this instead of axios/fetch directly.
 */

const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

/**
 * Creates an Acme-standard HTTP client with retry, tracing, and auth propagation.
 * @param {Object} config
 * @param {string} config.serviceName - Name of the calling service
 * @param {number} config.timeout - Request timeout in ms (default: 30000)
 * @param {number} config.maxRetries - Max retry attempts (default: 3)
 */
function createAcmeHttpClient(config) {
  const { serviceName, timeout = 30000, maxRetries = 3 } = config;

  const client = axios.create({
    timeout,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor: inject Acme headers
  client.interceptors.request.use((reqConfig) => {
    reqConfig.headers['X-Acme-Service'] = serviceName;
    reqConfig.headers['X-Acme-Request-ID'] = `acme-${uuidv4().replace(/-/g, '').slice(0, 16)}`;
    return reqConfig;
  });

  // Response interceptor: retry on 5xx
  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const config = error.config;
      if (!config) return Promise.reject(error);

      config._retryCount = config._retryCount || 0;
      if (config._retryCount >= maxRetries) {
        return Promise.reject(error);
      }

      const status = error.response?.status;
      if (status && status >= 500) {
        config._retryCount++;
        const delay = 100 * Math.pow(2, config._retryCount);
        await new Promise((resolve) => setTimeout(resolve, delay));
        return client(config);
      }

      return Promise.reject(error);
    }
  );

  return client;
}

module.exports = { createAcmeHttpClient };
