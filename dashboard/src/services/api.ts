import { API_BASE_URL } from '../constants';
import type { InventoryRequest, InventoryResponse } from '../types';

export async function fetchInventory(payload: InventoryRequest): Promise<InventoryResponse> {
  const response = await fetch(`${API_BASE_URL}/inventory/inventory`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let errorMessage = `HTTP error! status: ${response.status}`;
    
    if (errorData.detail) {
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail.map((err: { msg?: string }) => err.msg || JSON.stringify(err)).join(', ');
      } else {
        errorMessage = JSON.stringify(errorData.detail);
      }
    }
    
    throw new Error(errorMessage);
  }

  const responseText = await response.text();
  if (!responseText) {
    return {};
  }

  return JSON.parse(responseText) as InventoryResponse;
}

export async function testConnection(): Promise<{ message?: string }> {
  const response = await fetch(`${API_BASE_URL}/`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

