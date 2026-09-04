const API_BASE_URL = "http://127.0.0.1:8000";

async function fetchJSON(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function getSummary() {
  return fetchJSON("/summary");
}

export async function getInvestigations(priority = "HIGH") {
  return fetchJSON(
    `/investigations?priority=${encodeURIComponent(priority)}`
  );
}

export async function getFacilityDays() {
  return fetchJSON("/facility-days");
}

export async function getThermalObservations() {
  return fetchJSON("/thermal-observations");
}

export async function getFacilities() {
  return fetchJSON("/facilities");
}