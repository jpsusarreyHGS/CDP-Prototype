/**
 * Auth0 Configuration
 * 
 * For webpack, set these environment variables:
 * AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_AUDIENCE (optional)
 * 
 * Or configure them in webpack.config.js using DefinePlugin
 */

export const auth0Config = {
  domain: process.env.AUTH0_DOMAIN || '',
  clientId: process.env.AUTH0_CLIENT_ID || '',
  audience: process.env.AUTH0_AUDIENCE || undefined,
  // Use localStorage to persist auth state
  cacheLocation: 'localstorage' as const,
  // Enable refresh tokens
  useRefreshTokens: true,
};

// Validation
export const isAuth0Configured = (): boolean => {
  return !!(auth0Config.domain && auth0Config.clientId);
};

