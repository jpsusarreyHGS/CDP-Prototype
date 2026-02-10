// API Types
export interface Connection {
  type?: string;
  name?: string;
  project_id?: string;
  private_key_id?: string;
  private_key?: string;
  client_email?: string;
  client_id?: string;
  auth_uri?: string;
  token_uri?: string;
  auth_provider_x509_cert_url?: string;
  client_x509_cert_url?: string;
  universe_domain?: string;
  username?: string;
  password?: string;
  security_token?: string;
  access_token?: string;
}

export interface User {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  connections: Connection[];
}

export interface DateRange {
  start_date: string;
  end_date: string;
}

export interface Options {
  domain?: string;
  property_id?: string;
  fields?: string[];
  metrics?: string[];
  completeness_metric?: string;
  date_ranges?: DateRange[];
  object_names?: string[];
  object_types?: string[];
}

export interface InventoryRequest {
  user: User;
  options: Options;
}

export interface Field {
  name: string;
  non_null_count: number;
}

export interface PlatformData {
  entity: string;
  total_records: number;
  fields: Field[];
  platform?: string;
  _display_name?: string;
  metadata: any;
}

export type InventoryResponse = {
  [platformName: string]: PlatformData;
} & {
  _errors?: {
    [platform: string]: string;
  };
}

export type Platform = 'google_analytics' | 'salesforce' | 'hubspot';

// MFE Types
export interface MFEConfig {
  componentURL?: string;
  url?: string;
  componentName: string;
  componentClass: string;
  data?: Record<string, unknown>;
  config?: any;
  uiContext?: any;
}

