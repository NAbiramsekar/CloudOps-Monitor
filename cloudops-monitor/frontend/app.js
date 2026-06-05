const summaryFields = {
  application_status: document.querySelector("#application-status"),
  api_health_status: document.querySelector("#api-health-status"),
  total_requests: document.querySelector("#total-requests"),
  error_count: document.querySelector("#error-count"),
  cpu_usage: document.querySelector("#cpu-usage"),
  memory_usage: document.querySelector("#memory-usage"),
  active_incidents: document.querySelector("#active-incidents"),
};

const incidentsNode = document.querySelector("#incidents");
const form = document.querySelector("#incident-form");
const message = document.querySelector("#form-message");
const systemStatus = document.querySelector("#system-status");

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || response.statusText);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function titleCase(value) {
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const entities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return entities[character];
  });
}

async function loadSummary() {
  try {
    const summary = await requestJson("/dashboard/summary");
    summaryFields.application_status.textContent = titleCase(summary.application_status);
    summaryFields.api_health_status.textContent = titleCase(summary.api_health_status);
    summaryFields.total_requests.textContent = summary.total_requests;
    summaryFields.error_count.textContent = summary.error_count;
    summaryFields.cpu_usage.textContent = `${summary.cpu_usage.toFixed(1)}%`;
    summaryFields.memory_usage.textContent = `${summary.memory_usage.toFixed(1)}%`;
    summaryFields.active_incidents.textContent = summary.active_incidents;
    systemStatus.textContent = "Operational";
  } catch (error) {
    systemStatus.textContent = "Degraded";
  }
}

function incidentTemplate(incident) {
  const created = new Date(incident.created_time).toLocaleString();
  const incidentId = escapeHtml(incident.incident_id);
  return `
    <article class="incident">
      <div class="incident-header">
        <div>
          <h3>${escapeHtml(incident.title)}</h3>
          <p>${escapeHtml(incident.description)}</p>
        </div>
        <span class="badge">${incidentId}</span>
      </div>
      <div class="badges">
        <span class="badge severity-${escapeHtml(incident.severity)}">${escapeHtml(incident.severity)}</span>
        <span class="badge status-${escapeHtml(incident.status)}">${titleCase(escapeHtml(incident.status))}</span>
        <span class="badge">${created}</span>
      </div>
      <div class="actions">
        <button type="button" data-action="investigating" data-id="${incidentId}">Investigating</button>
        <button type="button" data-action="resolved" data-id="${incidentId}">Resolve</button>
        <button type="button" class="secondary" data-action="delete" data-id="${incidentId}">Delete</button>
      </div>
    </article>
  `;
}

async function loadIncidents() {
  const incidents = await requestJson("/incidents");
  incidentsNode.innerHTML = incidents.length
    ? incidents.map(incidentTemplate).join("")
    : '<div class="empty">No active incidents</div>';
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  try {
    await requestJson("/incidents", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    message.textContent = "Incident created.";
    await Promise.all([loadIncidents(), loadSummary()]);
  } catch (error) {
    message.textContent = error.message;
  }
});

incidentsNode.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const { action, id } = button.dataset;
  if (action === "delete") {
    await requestJson(`/incidents/${id}`, { method: "DELETE" });
  } else {
    await requestJson(`/incidents/${id}`, { method: "PUT", body: JSON.stringify({ status: action }) });
  }

  await Promise.all([loadIncidents(), loadSummary()]);
});

document.querySelector("#refresh-incidents").addEventListener("click", loadIncidents);

loadSummary();
loadIncidents();
setInterval(loadSummary, 10000);
