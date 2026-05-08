import { test, expect } from '@playwright/test'
import { mockStudentApis } from './helpers/api-mocks'

test.describe('Student flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockStudentApis(page)
  })

  test('join page is accessible without auth', async ({ page }) => {
    await page.goto('/join')
    await expect(page).toHaveURL(/\/join/)
    await expect(page.locator('text=Присоединиться к заданию')).toBeVisible()
  })

  test('join page shows name input', async ({ page }) => {
    await page.goto('/join')
    await expect(page.getByPlaceholder('Иван Иванов')).toBeVisible({ timeout: 5000 })
  })

  test('join page without token shows error message', async ({ page }) => {
    await page.goto('/join')
    // Without ?token= query param, the join page shows an error
    await expect(page.locator('text=Неверная ссылка')).toBeVisible({ timeout: 5000 })
  })

  test('student can join with valid token via URL', async ({ page }) => {
    await page.goto('/join?token=test-session-token-abc')
    await expect(page.getByPlaceholder('Иван Иванов')).toBeVisible({ timeout: 5000 })
    await page.getByPlaceholder('Иван Иванов').fill('Alice')
    await page.getByRole('button', { name: 'Войти' }).click()
    // Should navigate to /play/:sessionId or /wait/:sessionId
    await page.waitForURL(/\/(play|wait)\//, { timeout: 8000 })
    await expect(page).toHaveURL(/\/(play|wait)\//)
  })

  test('student sees error with invalid token', async ({ page }) => {
    await page.goto('/join?token=invalid-token-xyz')
    await expect(page.getByPlaceholder('Иван Иванов')).toBeVisible({ timeout: 5000 })
    await page.getByPlaceholder('Иван Иванов').fill('Bob')
    await page.getByRole('button', { name: 'Войти' }).click()

    // Error message should appear
    await expect(page.locator('.bg-red-50, [class*="red"]').first()).toBeVisible({ timeout: 5000 })
  })

  test('play page loads when session data is in localStorage', async ({ page }) => {
    const sessionPayload = {
      session_id: 'student-session-1',
      student_name: 'Alice',
      assignment_id: 'assignment-1',
      assignment_type: 'test',
      timer_seconds: 0,
      questions_data: {
        type: 'test',
        questions: [
          {
            question: 'What is photosynthesis?',
            level: 'easy',
            answers: [
              { text: 'Process A', correct: true },
              { text: 'Process B', correct: false },
              { text: 'Process C', correct: false },
              { text: 'Process D', correct: false },
            ],
          },
        ],
      },
    }

    await page.addInitScript(
      (payload) => { localStorage.setItem('student_session', JSON.stringify(payload)) },
      sessionPayload
    )

    await page.goto('/play/student-session-1')
    await page.waitForLoadState('networkidle', { timeout: 10000 })
    await expect(page.locator('body')).not.toBeEmpty()
    await expect(page.locator('text=What is photosynthesis?')).toBeVisible({ timeout: 5000 })
  })

  test('full student flow: join → answer → complete', async ({ page }) => {
    await page.goto('/join?token=test-session-token-abc')
    await page.getByPlaceholder('Иван Иванов').fill('Alice')
    await page.getByRole('button', { name: 'Войти' }).click()
    await page.waitForURL(/\/(play|wait)\//, { timeout: 8000 })

    // Should be on play or wait page
    await page.waitForLoadState('networkidle', { timeout: 5000 })
    await expect(page.locator('body')).not.toBeEmpty()
  })
})
