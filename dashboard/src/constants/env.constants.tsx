export const apiUrls = {
  AUTH_URL: process.env.AUTH_URL as string,
  APP_ENVIRONMENT: process.env.APP_ENVIRONMENT as string,
  AUTH0_DOMAIN: process.env.AUTH0_DOMAIN as string,
  AUTH0_CLIENT_ID: process.env.AUTH0_CLIENT_ID as string,
  AUTH0_AUDIENCE: process.env.AUTH0_AUDIENCE as string,
  AUTH0_CONNECTION: process.env.AUTH0_CONNECTION as string,
  BACK_OFFICE_CONFIG_URL: process.env.BACK_OFFICE_CONFIG_URL as string,
  AUTH0_ORGANIZATIONS_ID: process.env.AUTH0_ORGANIZATIONS_ID as string,
  AUTH0_ORGANIZATIONS_CLIENT_ID: process.env
    .AUTH0_ORGANIZATIONS_CLIENT_ID as string,
  AUTH0_ORGANIZATIONS_AUDIENCE: process.env
    .AUTH0_ORGANIZATIONS_AUDIENCE as string,
  AUTH0_ORGANIZATIONS_DOMAIN: process.env.AUTH0_ORGANIZATIONS_DOMAIN as string,
};

export const FEATURE_TOGGLES = {
  DYNAMIC_CLIENT_ID: process.env.FEATURE_TOGGLES_DYNAMIC_CLIENT_ID
    ? process.env.FEATURE_TOGGLES_DYNAMIC_CLIENT_ID.toLowerCase() === 'true'
    : false,
  ENABLE_AUTH0_ORGANIZATION: process.env
    .FEATURE_TOGGLES_ENABLE_AUTH0_ORGANIZATION
    ? process.env.FEATURE_TOGGLES_ENABLE_AUTH0_ORGANIZATION.toLowerCase() ===
      'true'
    : false,
  ENABLE_AUTH0_LOCAL_STORAGE_USAGE: process.env
    .FEATURE_TOGGLES_ENABLE_AUTH0_LOCAL_STORAGE_USAGE
    ? process.env.FEATURE_TOGGLES_ENABLE_AUTH0_LOCAL_STORAGE_USAGE.toLowerCase() ===
      'true'
    : false,
};
