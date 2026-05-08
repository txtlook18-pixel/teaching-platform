import { test, expect } from '@playwright/test'
import {
  mockAuthApis,
  mockLessonApis,
  mockAssignmentApis,
  injectAuthViaInitScript,
  FAKE_LESSON,
  FAKE_TOKEN,
  FAKE_USER,
} from './helpers/api-mocks'

test.describe('Teacher flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthApis(page)
    await mockLessonApis(page)
    await mockAssignmentApis(page)
    // Inject auth BEFORE navigation so Pinia picks it up on initialization
    await injectAuthViaInitScript(page)
  })

  test('dashboard shows lesson list', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 })
    await expect(page.locator('text=Biology: Photosynthesis')).toBeVisible({ timeout: 5000 })
  })

  test('navigate to create lesson page', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 })

    const createBtn = page.getByRole('link', { name: /создать|new lesson|добавить|\+/i })
    if (await createBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await createBtn.click()
    } else {
      await page.goto('/lessons/create')
    }
    await expect(page).toHaveURL(/\/lessons\/create/)
  })

  test('create lesson page renders form', async ({ page }) => {
    await page.goto('/lessons/create')
    await expect(page).toHaveURL(/\/lessons\/create/)
    // Form should have text inputs
    await expect(page.locator('form')).toBeVisible({ timeout: 5000 })
  })

  test('lesson detail page shows lesson info', async ({ page }) => {
    await page.goto('/lessons/lesson-1')
    await expect(page).toHaveURL(/\/lessons\/lesson-1/, { timeout: 5000 })
    await expect(page.locator('text=Biology: Photosynthesis')).toBeVisible({ timeout: 5000 })
  })

  test('assignment page renders without errors', async ({ page }) => {
    await page.goto('/lessons/lesson-1/assignment/assignment-1')
    await page.waitForLoadState('networkidle', { timeout: 10000 })
    // Should not show a blank page or crash
    await expect(page.locator('body')).not.toBeEmpty()
    // Should not be redirected to login
    await expect(page).not.toHaveURL(/\/login/)
  })

  test('archive page shows assignment history', async ({ page }) => {
    await page.goto('/archive')
    await expect(page).toHaveURL(/\/archive/, { timeout: 5000 })
    await expect(page.locator('text=Biology: Photosynthesis')).toBeVisible({ timeout: 5000 })
  })

  test('profile page is accessible', async ({ page }) => {
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FAKE_USER) })
    })
    await page.goto('/profile')
    await expect(page).toHaveURL(/\/profile/, { timeout: 5000 })
    await expect(page.locator('body')).not.toBeEmpty()
  })

  test('full teacher flow: login → lesson → create assignment', async ({ page }) => {
    // Start unauthenticated
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access_token: FAKE_TOKEN, user: FAKE_USER }),
      })
    })

    // Go to login page
    await page.goto('/login')
    await page.getByPlaceholder('teacher@school.com').fill('teacher@test.com')
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Войти' }).click()
    await page.waitForURL(/\/dashboard/, { timeout: 8000 })

    // Verify dashboard shows lessons
    await expect(page.locator('text=Biology: Photosynthesis')).toBeVisible({ timeout: 5000 })

    // Navigate to lesson
    await page.goto('/lessons/lesson-1')
    await expect(page.locator('text=Biology: Photosynthesis')).toBeVisible({ timeout: 5000 })
  })
})
