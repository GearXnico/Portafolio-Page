// Página vacía de la plantilla. React y TypeScript llegan en la tarea 1.3 del plan.
const status = document.querySelector("#api-status");

fetch("/api/health")
  .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
  .then((body) => {
    status.textContent = body.status;
  })
  .catch(() => {
    status.textContent = "sin respuesta";
  });
