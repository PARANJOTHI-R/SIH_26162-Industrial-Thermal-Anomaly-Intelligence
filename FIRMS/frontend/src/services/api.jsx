const API_BASE_URL = "http://127.0.0.1:8000";

async function fetchJSON(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function getRegions() {
  return fetchJSON("/regions");
}

export async function getSummary(region = "jamnagar") {
  return fetchJSON(`/summary?region=${encodeURIComponent(region)}`);
}

export async function getInvestigations(region = "jamnagar", priority = "HIGH") {
  return fetchJSON(
    `/investigations?region=${encodeURIComponent(region)}&priority=${encodeURIComponent(priority)}`
  );
}

export async function getFacilityDays(region = "jamnagar") {
  return fetchJSON(`/facility-days?region=${encodeURIComponent(region)}`);
}

export async function getThermalObservations(region = "jamnagar") {
  return fetchJSON(`/thermal-observations?region=${encodeURIComponent(region)}`);
}

export async function getThermalEvents(region = "jamnagar") {
  return fetchJSON(`/thermal-events?region=${encodeURIComponent(region)}`);
}

export async function getFacilities(region = "jamnagar") {
  return fetchJSON(`/facilities?region=${encodeURIComponent(region)}`);
}

export async function getUnknownSources(region = "jamnagar") {
  return fetchJSON(`/unknown-sources?region=${encodeURIComponent(region)}`);
}