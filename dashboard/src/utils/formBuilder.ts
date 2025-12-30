import type { Platform, InventoryRequest, Connection, Options } from '../types';
import { GA4_METRICS } from '../constants';

interface FormData {
  // GA fields
  gaType: string;
  gaProjectId: string;
  gaPrivateKeyId: string;
  gaPrivateKey: string;
  gaClientEmail: string;
  gaClientId: string;
  gaAuthUri: string;
  gaTokenUri: string;
  gaAuthProviderCertUrl: string;
  gaClientCertUrl: string;
  gaUniverseDomain: string;
  gaPropertyId: string;
  gaFields: string;
  gaStartDate: string;
  gaEndDate: string;
  // Salesforce fields
  sfUsername: string;
  sfPassword: string;
  sfSecurityToken: string;
  sfDomain: string;
  // HubSpot fields
  hsAccessToken: string;
}

export function buildRequestPayload(platform: Platform, formData: FormData): InventoryRequest {
  console.log('Building payload for platform:', platform);
  
  const user = {
    first_name: "string",
    last_name: "string",
    email: "string",
    phone: "string",
    connections: [] as Connection[]
  };
  
  const options: Options = {
    domain: "test"
  };
  
  if (platform === 'google_analytics') {
    // Escape newlines in private key
    const privateKey = formData.gaPrivateKey.replace(/\n/g, '\\n');
    
    user.connections.push({
      type: formData.gaType,
      project_id: formData.gaProjectId,
      private_key_id: formData.gaPrivateKeyId,
      private_key: privateKey,
      client_email: formData.gaClientEmail,
      client_id: formData.gaClientId,
      auth_uri: formData.gaAuthUri,
      token_uri: formData.gaTokenUri,
      auth_provider_x509_cert_url: formData.gaAuthProviderCertUrl,
      client_x509_cert_url: formData.gaClientCertUrl,
      universe_domain: formData.gaUniverseDomain
    });
    
    options.property_id = formData.gaPropertyId;
    const fields = formData.gaFields.split(',').map(f => f.trim()).filter(f => f);
    
    const startDate = formData.gaStartDate;
    const endDate = formData.gaEndDate;
    if (startDate && endDate) {
      options.date_ranges = [{
        start_date: startDate,
        end_date: endDate
      }];
    }
    
    const baseFields = fields.length > 0 ? fields : ['userPseudoId', 'sessionSource', 'eventName'];
    const allFields = [...new Set([...baseFields, ...GA4_METRICS])];
    
    options.fields = allFields;
    options.metrics = ['totalUsers'];
    options.completeness_metric = 'totalUsers';
    
  } else if (platform === 'salesforce') {
    const username = formData.sfUsername.trim();
    const password = formData.sfPassword.trim();
    const securityToken = formData.sfSecurityToken.trim();
    const domain = formData.sfDomain || 'login';
    
    if (!username || !password || !securityToken) {
      throw new Error('All Salesforce credentials are required (Username, Password, Security Token)');
    }
    
    user.connections.push({
      name: 'salesforce',
      username: username,
      password: password,
      security_token: securityToken
    });
    
    options.domain = domain;
    options.object_names = ['Contact', 'Case'];
    
  } else if (platform === 'hubspot') {
    let accessToken = formData.hsAccessToken.trim();
    if (!accessToken) {
      throw new Error('HubSpot access token is required. Please enter a valid access token.');
    }
    
    accessToken = String(accessToken);
    
    if ((accessToken.startsWith('"') && accessToken.endsWith('"')) || 
        (accessToken.startsWith("'") && accessToken.endsWith("'"))) {
      accessToken = accessToken.slice(1, -1);
    }
    
    user.connections.push({
      name: 'hubspot',
      access_token: accessToken
    });
    
    options.object_types = ['contacts', 'deals'];
  }
  
  const payload: InventoryRequest = { user, options };
  console.log('Final payload:', JSON.stringify(payload, null, 2));
  return payload;
}

