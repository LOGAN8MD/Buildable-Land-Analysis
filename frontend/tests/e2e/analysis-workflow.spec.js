import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('https://basemaps.cartocdn.com/**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ version: 8, sources: {}, layers: [] }),
    });
  });
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('39.39 acres')).toBeVisible();
  await expect(page.getByText('10.00 acres')).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Why' })).toBeVisible();
  await expect(page.getByText('Mapped NWI wetland plus 50-ft planning setback')).toBeVisible();
});

test('loads analysis, toggles a layer, and recalculates a buffer', async ({ page }) => {
  const buildingToggle = page.getByLabel('Buildings');
  await expect(buildingToggle).toBeChecked();
  await buildingToggle.evaluate((element) => element.click());
  await expect(buildingToggle).not.toBeChecked();

  const wetlandBuffer = page.locator('input[name="wetlands"]');
  const analysisResponse = page.waitForResponse(
    (response) => response.url().endsWith('/api/v1/analysis') && response.ok()
  );
  await wetlandBuffer.fill('0');
  await page.getByRole('button', { name: 'Run Analysis' }).click();
  await analysisResponse;
  await expect(wetlandBuffer).toHaveValue('0');
});

test('selecting another parcel reruns analysis and fits the new result', async ({ page }) => {
  const selector = page.getByLabel('Select Parcel');
  await expect(selector.locator('option')).toHaveCount(3);
  const analysisResponse = page.waitForResponse(
    (response) => response.url().endsWith('/api/v1/analysis') && response.ok()
  );
  await selector.selectOption('parcel-283139');
  await analysisResponse;
  await expect(selector).toHaveValue('parcel-283139');
  await expect(page.getByText('28.88 acres')).toBeVisible();
  await expect(page.getByText('COMMERCIAL IMPROVED | 21.48 source acres')).toBeVisible();
});

test('exclude and restore accept the same polygon without validation errors', async ({ page, request }) => {
  await page.getByRole('button', { name: 'Restore Area' }).click();
  await expect(page.getByText('Draw polygons to restore previously excluded areas.')).toBeVisible();

  const analysisResponse = await request.post('http://127.0.0.1:8001/api/v1/analysis', {
    data: {
      parcel_id: 'parcel',
      constraints: ['wetlands', 'floodzones', 'buildings'],
      buffers: { wetlands: 50, floodzones: 0, buildings: 20 },
    },
  });
  expect(analysisResponse.ok()).toBeTruthy();
  const analysis = await analysisResponse.json();
  const geometry = {
    type: 'FeatureCollection',
    features: [{
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [-97.723918, 30.249230],
          [-97.723907, 30.249230],
          [-97.723907, 30.249241],
          [-97.723918, 30.249241],
          [-97.723918, 30.249230],
        ]],
      },
    }],
  };

  const editPayload = {
    geometry,
    current_buildable: analysis.buildable_geometry,
    current_excluded: analysis.excluded_geometry,
    parcel_geometry: analysis.parcel_geometry,
    constraint_geometries: analysis.constraint_geometries,
    breakdown: analysis.breakdown,
  };
  const excludeResponse = await request.post('http://127.0.0.1:8001/api/v1/exclude', {
    data: { ...editPayload, edit_type: 'exclude' },
  });
  expect(excludeResponse.ok(), await excludeResponse.text()).toBeTruthy();
  const excluded = await excludeResponse.json();
  expect(excluded.breakdown.at(-1).layer_name).toBe('User Exclude');
  expect(excluded.breakdown.at(-1).reason).toBe('Manually removed from currently buildable land');

  const restoreResponse = await request.post('http://127.0.0.1:8001/api/v1/restore', {
    data: {
      ...editPayload,
      edit_type: 'restore',
      current_buildable: excluded.buildable_geometry,
      current_excluded: excluded.excluded_geometry,
      breakdown: excluded.breakdown,
    },
  });
  expect(restoreResponse.ok(), await restoreResponse.text()).toBeTruthy();
  const restored = await restoreResponse.json();
  expect(restored.breakdown.at(-1).layer_name).toBe('User Restore');
  expect(restored.breakdown.at(-1).reason).toBe('Manually restored from previously excluded land');
});
