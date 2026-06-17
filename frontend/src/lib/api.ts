import { SearchResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function searchByText(
  query: string,
  measurements?: Record<string, number>,
  gender?: string
): Promise<SearchResponse> {
  const formData = new FormData();
  formData.append('query', query);
  if (measurements) {
    formData.append('measurements_json', JSON.stringify(measurements));
  }
  if (gender && gender !== 'any') {
    formData.append('gender', gender);
  }

  const response = await fetch(`${API_BASE}/api/search/text`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP error! Status: ${response.status}`);
  }

  return response.json();
}

export async function searchByImage(
  file: File,
  measurements?: Record<string, number>,
  gender?: string
): Promise<SearchResponse> {
  const formData = new FormData();
  formData.append('image', file);
  if (measurements) {
    formData.append('measurements_json', JSON.stringify(measurements));
  }
  if (gender && gender !== 'any') {
    formData.append('gender', gender);
  }

  const response = await fetch(`${API_BASE}/api/search/visual`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP error! Status: ${response.status}`);
  }

  return response.json();
}
