/**
 * @file config.ts
 */

import { apiUrls, FEATURE_TOGGLES } from './constants/env.constants';

class Config {
  refreshRate: number;
  AUTH_URL: string;
  AUTH0_DOMAIN: string;
  AUTH0_CLIENT_ID: string;
  AUTH0_AUDIENCE: string;
  AUTH0_CONNECTION: string;
  configFile: string;
  assetPath: string;

  constructor() {
    let ENVIRONMENT: string;
    if (typeof apiUrls.APP_ENVIRONMENT === 'undefined') {
      ENVIRONMENT = 'local';
    } else {
      ENVIRONMENT = apiUrls.APP_ENVIRONMENT;
    }
    this.configFile = '';

    this.refreshRate = 30000; // 30sec (in milliseconds)
    this.assetPath = 'https://agentx-assets.hgsdigital.com/assets';
    /** Auth0 constants */
    this.AUTH_URL = apiUrls.AUTH_URL;
    this.AUTH0_DOMAIN = apiUrls.AUTH0_DOMAIN;
    this.AUTH0_CLIENT_ID = apiUrls.AUTH0_CLIENT_ID;
    this.AUTH0_AUDIENCE = apiUrls.AUTH0_AUDIENCE;
    this.AUTH0_CONNECTION = apiUrls.AUTH0_CONNECTION;

    if (FEATURE_TOGGLES.DYNAMIC_CLIENT_ID) {
      if (apiUrls.APP_ENVIRONMENT === 'local') {
        // Use the below two lines for localhost:8000
        const configServer = 'http://localhost:8027/json-contract/config.json';
        this.configFile = configServer;
      } else {
        this.configFile = apiUrls.BACK_OFFICE_CONFIG_URL;
      }
    } else {
      if (apiUrls.APP_ENVIRONMENT === 'dev') {
        this.configFile =
          'https://agentx-dev.hgsdigital.com/api/backoffice/v1/module/config?moduleName=AskAnything&clientId=HGSDEV';
      } else if (apiUrls.APP_ENVIRONMENT === 'qa') {
        this.configFile =
          'https://agentx-qa.hgsdigital.com/api/backoffice/v1/module/config?moduleName=AskAnything&clientId=HGSQA';
      } else if (apiUrls.APP_ENVIRONMENT === 'prod') {
        this.configFile =
          'https://agentx-core.s3.amazonaws.com/prod/component/config.json?clientId=hgsDemoDevelopment&moduleName=AskAnything';
      } else if (apiUrls.APP_ENVIRONMENT === 'local') {
        this.configFile = 'http://localhost:8027/json-contract/config.json';
      }
    }
  }
}

export default new Config();
