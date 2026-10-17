import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FIXTURES_DIR = path.join(__dirname, 'fixtures');
const VALID_ZIP_PATH = path.join(FIXTURES_DIR, 'valid_project.zip');
const INVALID_FILE_PATH = path.join(FIXTURES_DIR, 'invalid_file.txt');

// Standard mock responses for isolated test environment
const MOCK_HEALTH = { status: 'healthy', version: '1.0.0', project_count: 0, telemetry_events_count: 0 };
const MOCK_PROJECT_METADATA = {
  project_id: 'proj-e2e-test',
  name: 'valid_project',
  status: 'ready',
  file_count: 3,
  extracted_size_bytes: 1024,
  detected_languages: ['JavaScript'],
  detected_frameworks: ['Node.js'],
  capabilities: ['static_analysis', 'ast_parser'],
  excluded_items_count: 0,
};

test.describe('SENTINEL Browser End-to-End Smoke Test Suite', () => {

  test('1. Application loads and transitions to project entry screen', async ({ page }) => {
    // Intercept initial bootstrap endpoints
    await page.route('**/api/health', (route) => route.fulfill({ json: MOCK_HEALTH }));
    await page.route('**/api/projects', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/incidents', (route) => route.fulfill({ json: [] }));

    await page.goto('/');

    // Verify Project Entry screen rendered
    const title = page.locator('h1', { hasText: 'SENTINEL' });
    await expect(title).toBeVisible();

    const subtitle = page.locator('text=Understand your code. Investigate failures. Validate improvements.');
    await expect(subtitle).toBeVisible();

    // Verify Dropzone is visible
    const dropzone = page.locator('text=Drag & Drop Project ZIP');
    await expect(dropzone).toBeVisible();
  });

  test('2. Invalid upload is rejected and START PROJECT remains disabled', async ({ page }) => {
    await page.route('**/api/health', (route) => route.fulfill({ json: MOCK_HEALTH }));
    await page.route('**/api/projects', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/incidents', (route) => route.fulfill({ json: [] }));

    await page.goto('/');

    // Select invalid file (.txt)
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(INVALID_FILE_PATH);

    // Verify error banner is visible with expected warning
    const errorBanner = page.locator('text=Invalid file type: Please select a valid .zip project archive');
    await expect(errorBanner).toBeVisible();

    // Verify START PROJECT button is disabled
    const startBtn = page.getByRole('button', { name: /START PROJECT/i });
    await expect(startBtn).toBeDisabled();
  });

  test('3. Valid test ZIP is selected, uploaded, and enables START PROJECT', async ({ page }) => {
    await page.route('**/api/health', (route) => route.fulfill({ json: MOCK_HEALTH }));
    await page.route('**/api/projects', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/incidents', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/projects/upload', (route) => route.fulfill({ json: MOCK_PROJECT_METADATA }));

    await page.goto('/');

    // Select valid .zip fixture
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(VALID_ZIP_PATH);

    // Click "Upload & Validate"
    const uploadBtn = page.getByRole('button', { name: 'Upload & Validate' });
    await expect(uploadBtn).toBeVisible();
    await uploadBtn.click();

    // Verify upload success banner
    const successMsg = page.locator('text=Project archive successfully validated and isolated in workspace');
    await expect(successMsg).toBeVisible();

    // START PROJECT button should now be enabled
    const startBtn = page.getByRole('button', { name: /START PROJECT/i });
    await expect(startBtn).toBeEnabled();
  });

  test('4. Starting project reaches five-feature dashboard and opens all 5 workspaces', async ({ page }) => {
    await page.route('**/api/health', (route) => route.fulfill({ json: MOCK_HEALTH }));
    await page.route('**/api/projects', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/incidents', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/projects/upload', (route) => route.fulfill({ json: MOCK_PROJECT_METADATA }));
    await page.route('**/api/projects/**/inspect', (route) => route.fulfill({
      json: {
        project_id: 'proj-e2e-test',
        status: 'ready',
        capabilities: ['static_analysis', 'ast_parser'],
        inspected_at: Date.now(),
      }
    }));
    await page.route('**/api/projects/proj-e2e-test', (route) => route.fulfill({ json: MOCK_PROJECT_METADATA }));

    // Mock individual workspace API endpoints to avoid unhandled network failures
    await page.route('**/api/projects/**/compatibility', (route) => route.fulfill({ status: 404, json: { detail: 'Not cached' } }));
    await page.route('**/api/projects/**/audit', (route) => route.fulfill({ status: 404, json: { detail: 'Not cached' } }));
    await page.route('**/api/compatibility/**', (route) => route.fulfill({
      json: {
        project_id: 'proj-e2e-test',
        overall_status: 'compatible',
        readiness_score: 95,
        detected_technologies: [{ category: 'language', name: 'JavaScript', version: 'ES2024', confidence: 'HIGH', evidence_files: ['index.js'] }],
        prerequisites: [],
        telemetry_readiness: { score: 80, readiness_level: 'READY', sources_found: ['console.log'], recommended_integrations: [] },
        next_steps: ['Run test suite'],
      }
    }));
    await page.route('**/api/audit/**', (route) => route.fulfill({
      json: {
        project_id: 'proj-e2e-test',
        total_claims: 2,
        verified_count: 1,
        partially_implemented_count: 1,
        contradicted_count: 0,
        unverifiable_count: 0,
        results: [],
      }
    }));
    await page.route('**/api/radar/**', (route) => route.fulfill({
      json: {
        nodes: [{ id: 'order-service', service: 'order-service', tier: 'Service', status: 'healthy', error_count: 0, total_requests: 10 }],
        edges: [],
        suspected_component: 'order-service',
        impacted_components: [],
        dependency_paths: [],
        supporting_evidence: [],
        suggested_investigation_steps: [],
      }
    }));
    await page.route('**/api/validation/**', (route) => route.fulfill({
      json: [
        {
          id: 'db_pool_exhaustion',
          name: 'Database Connection Pool Exhaustion',
          target_service: 'inventory-service',
          description: 'Hikari connection pool saturation on inventory-service',
          expected_failure: 'HikariPool-1 - Connection is not available, request timed out (maxPoolSize=10)',
          available_fixes: [
            {
              id: 'increase_pool_size',
              title: 'Expand Database Pool Limits',
              description: 'Scale Hikari pool maximum capacity',
              risk_level: 'LOW',
              configuration_diff: '+ datasource.hikari.maximum-pool-size: 30'
            }
          ]
        }
      ]
    }));

    await page.goto('/');

    // Upload project and start
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(VALID_ZIP_PATH);
    await page.getByRole('button', { name: 'Upload & Validate' }).click();

    const startBtn = page.getByRole('button', { name: /START PROJECT/i });
    await expect(startBtn).toBeEnabled();
    await startBtn.click();

    // Verify reached Five-Feature Dashboard
    await expect(page.locator('text=Select Developer Intelligence Workspace')).toBeVisible();

    // Feature 1: Compatibility
    const feat1 = page.locator('.feature-card', { hasText: 'Can I use it?' });
    await feat1.click();
    await expect(page.locator('text=Feature 1 — Project Compatibility & Integration Readiness')).toBeVisible();
    await page.getByRole('button', { name: /Back to Dashboard/i }).click();
    await expect(page.locator('text=Select Developer Intelligence Workspace')).toBeVisible();

    // Feature 2: Promise vs Reality Audit
    const feat2 = page.locator('.feature-card', { hasText: 'Have I built what I promised?' });
    await feat2.click();
    await expect(page.locator('text=Feature 2 — Promise vs. Reality Code Audit')).toBeVisible();
    await page.getByRole('button', { name: /Back to Dashboard/i }).click();
    await expect(page.locator('text=Select Developer Intelligence Workspace')).toBeVisible();

    // Feature 3: Live Incident Investigation
    const feat3 = page.locator('.feature-card', { hasText: 'Why is my application failing?' });
    await feat3.click();
    await expect(page.locator('text=Feature 3 — Live Incident Investigation')).toBeVisible();
    await page.getByRole('button', { name: /Back to Dashboard/i }).click();
    await expect(page.locator('text=Select Developer Intelligence Workspace')).toBeVisible();

    // Feature 4: Dependency & Impact Radar
    const feat4 = page.locator('.feature-card', { hasText: 'What else could break?' });
    await feat4.click();
    await expect(page.locator('text=Feature 4 — Dependency & Impact Radar')).toBeVisible();
    await page.getByRole('button', { name: /Back to Dashboard/i }).click();
    await expect(page.locator('text=Select Developer Intelligence Workspace')).toBeVisible();

    // Feature 5: Replay Lab & Fix Validation
    const feat5 = page.locator('.feature-card', { hasText: 'Does my fix actually work?' });
    await feat5.click();
    await expect(page.locator('text=Feature 5 — Replay Lab & Controlled Fix Validation')).toBeVisible();
    await page.getByRole('button', { name: /Back to Dashboard/i }).click();
    await expect(page.locator('text=Select Developer Intelligence Workspace')).toBeVisible();
  });

  test('5. Failed API requests produce a useful error state', async ({ page }) => {
    await page.route('**/api/health', (route) => route.fulfill({ json: MOCK_HEALTH }));
    await page.route('**/api/projects', (route) => route.fulfill({ json: [] }));
    await page.route('**/api/incidents', (route) => route.fulfill({ json: [] }));
    
    // Simulate backend rejection (e.g. 500 Internal Error)
    await page.route('**/api/projects/upload', (route) => route.fulfill({
      status: 500,
      json: { detail: 'Corrupt archive stream: Unexpected EOF in central directory' }
    }));

    await page.goto('/');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(VALID_ZIP_PATH);

    const uploadBtn = page.getByRole('button', { name: 'Upload & Validate' });
    await uploadBtn.click();

    // Verify error banner is displayed with the failure detail
    const errorBanner = page.locator('text=Corrupt archive stream: Unexpected EOF in central directory');
    await expect(errorBanner).toBeVisible();

    // Verify START PROJECT button remains disabled
    const startBtn = page.getByRole('button', { name: /START PROJECT/i });
    await expect(startBtn).toBeDisabled();
  });

});
