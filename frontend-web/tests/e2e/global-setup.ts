import { FullConfig } from "@playwright/test";

const SERVICES = {
  "Auth Service": "http://localhost:8001/health",
  "Academic Service": "http://localhost:8002/health",
  "Logbook Service": "http://localhost:8006/health",
  "Institution Service": "http://localhost:8007/health",
  "Workflow Service": "http://localhost:8010/health",
};

async function globalSetup(config: FullConfig) {
  console.log("\n====================================================");
  console.log("    PLAYWRIGHT GLOBAL SETUP: HEALTH CHECKING...     ");
  console.log("====================================================");

  const errors: string[] = [];

  for (const [name, url] of Object.entries(SERVICES)) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(3000) });
      if (response.ok) {
        console.log(`  [OK] ${name} is reachable and healthy (${url})`);
      } else {
        const statusText = response.statusText || `status ${response.status}`;
        errors.push(`${name} at ${url} returned status ${response.status}`);
      }
    } catch (err: any) {
      errors.push(`${name} at ${url} is unreachable: ${err.message || err}`);
    }
  }

  if (errors.length > 0) {
    console.error("\n====================================================");
    console.error("❌ E2E TESTING BLOCKED: BACKEND SERVICES UNHEALTHY");
    errors.forEach((err) => console.error(`  - ${err}`));
    console.error(
      "\nPlease make sure all docker compose containers are running.",
    );
    console.error("Run command: docker compose --profile services up -d");
    console.error("====================================================\n");
    throw new Error(
      "One or more backend services are unhealthy or unreachable. Aborting test execution.",
    );
  }

  console.log("====================================================\n");
}

export default globalSetup;
