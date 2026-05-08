import { test, expect } from '@playwright/test'
import { mockAuthApis, mockLessonApis, injectAuthViaInitScript } from './helpers/api-mocks'

test.describe('Authentication', () => {
  test('login page renders for unauthenticated users', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveURL(/\/login/)
    // LoginPage shows h1 "AI Teaching Platform" and p "Войдите в аккаунт"
    await expect(page.locator('text=Войдите в аккаунт')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Войти' })).toBeVisible()
  })

  test('dashboard redirects unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })

  test('register form submits and redirects to dashboard', async ({ page }) => {
    await mockAuthApis(page)
    await mockLessonApis(page)

    await page.goto('/register')
    await expect(page.locator('text=Создать аккаунт')).toBeVisible()

    await page.getByPlaceholder('Иван Иванов').first().fill('Test Teacher')
    await page.getByPlaceholder('teacher@school.com').fill('teacher@test.com')
    await page.getByPlaceholder('Минимум 6 символов').fill('secret123')

    await page.getByRole('button', { name: 'Зарегистрироваться' }).click()
    await page.waitForURL(/\/dashboard/, { timeout: 8000 })
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('login form submits and redirects to dashboard', async ({ page }) => {
    await mockAuthApis(page)
    await mockLessonApis(page)

    await page.goto('/login')
    await page.getByPlaceholder('teacher@school.com').fill('teacher@test.com')
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Войти' }).click()
    await page.waitForURL(/\/dashboard/, { timeout: 8000 })
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('invalid login keeps user on login page', async ({ page }) => {
    // Use 400 instead of 401 to avoid the api.ts interceptor hard-redirecting to /login
    // (401 interceptor is for expired session tokens, not invalid credentials)
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Неверный email или пароль' }),
      })
    })

    await page.goto('/login')
    await page.getByPlaceholder('teacher@school.com').fill('wrong@test.com')
    await page.locator('input[type="password"]').fill('wrongpass')
    await page.getByRole('button', { name: 'Войти' }).click()

    // Error message appears in the form
    await expect(page.locator('text=Неверный email или пароль')).toBeVisible({ timeout: 5000 })
    // User stays on login page
    await expect(page).toHaveURL(/\/login/)
  })

  test('authenticated user stays on dashboard', async ({ page }) => {
    await mockAuthApis(page)
    await mockLessonApis(page)
    await injectAuthViaInitScript(page)

    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 })
    // Should NOT be redirected to login
    await expect(page).not.toHaveURL(/\/login/)
  })
})
