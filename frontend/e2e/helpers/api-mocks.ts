import { Page, BrowserContext } from '@playwright/test'

export const FAKE_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEiLCJleHAiOjk5OTk5OTk5OTl9.fake'

export const FAKE_USER = {
  id: 'user-1',
  email: 'teacher@test.com',
  username: 'Test Teacher',
}

export const FAKE_LESSON = {
  id: 'lesson-1',
  title: 'Biology: Photosynthesis',
  language: 'en',
  source_type: 'text',
  source_content: 'Photosynthesis is the process by which plants convert sunlight into food.',
  teacher_id: 'user-1',
  cluster_data: {
    main_topic: 'Photosynthesis',
    subtopics: ['Light reactions', 'Calvin cycle'],
    key_concepts: ['chlorophyll', 'ATP', 'glucose'],
    difficulty_estimate: 'intermediate',
    suggested_question_count: 10,
  },
  created_at: '2026-05-08T10:00:00Z',
}

export const FAKE_ASSIGNMENT = {
  id: 'assignment-1',
  lesson_id: 'lesson-1',
  assignment_type: 'test',
  status: 'draft',
  question_count: 5,
  timer_seconds: 30,
  questions_data: null,
  session_token: null,
  created_at: '2026-05-08T10:00:00Z',
}

export async function mockAuthApis(page: Page) {
  await page.route('**/api/v1/auth/register', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access_token: FAKE_TOKEN, user: FAKE_USER }),
    })
  })
  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access_token: FAKE_TOKEN, user: FAKE_USER }),
    })
  })
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(FAKE_USER),
    })
  })
}

export async function mockLessonApis(page: Page) {
  await page.route('**/api/v1/lessons/', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([FAKE_LESSON]) })
    } else if (route.request().method() === 'POST') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FAKE_LESSON) })
    } else {
      await route.continue()
    }
  })
  await page.route('**/api/v1/lessons/lesson-1', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FAKE_LESSON) })
  })
  await page.route('**/api/v1/lessons/lesson-1/analyze', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FAKE_LESSON) })
  })
  await page.route('**/api/v1/lessons/lesson-1/assignments', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([FAKE_ASSIGNMENT]) })
  })
}

export async function mockAssignmentApis(page: Page) {
  await page.route('**/api/v1/assignments/lessons/lesson-1/assignments', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FAKE_ASSIGNMENT) })
  })
  await page.route('**/api/v1/assignments/assignment-1', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ...FAKE_ASSIGNMENT,
        status: 'active',
        session_token: 'test-session-token-abc',
        questions_data: {
          type: 'test',
          questions: [
            { question: 'What is photosynthesis?', options: ['A', 'B', 'C', 'D'], correct: 'A', difficulty: 'easy', explanation: '...' },
          ],
        },
      }),
    })
  })
  await page.route('**/api/v1/assignments/assignment-1/generate', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'generated', assignment_id: 'assignment-1' }) })
  })
  await page.route('**/api/v1/assignments/assignment-1/activate', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ session_token: 'test-session-token-abc', assignment_id: 'assignment-1', expires_at: '2026-05-09T10:00:00Z' }),
    })
  })
  await page.route('**/api/v1/assignments/assignment-1/results', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        assignment_id: 'assignment-1',
        student_count: 1,
        sessions: [{ id: 'session-1', student_name: 'Alice', joined_at: '2026-05-08T10:05:00Z' }],
        responses: [],
      }),
    })
  })
  await page.route('**/api/v1/assignments/assignment-1/finish', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'finished' }) })
  })
  await page.route('**/api/v1/assignments/history', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 'assignment-1', lesson_title: 'Biology: Photosynthesis', assignment_type: 'test', status: 'finished', student_count: 1, response_count: 0, created_at: '2026-05-08T10:00:00Z' },
      ]),
    })
  })
}

export async function mockStudentApis(page: Page) {
  await page.route('**/api/v1/assignments/join', async (route) => {
    const body = JSON.parse(route.request().postData() || '{}')
    if (body.session_token === 'test-session-token-abc') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'student-session-1',
          student_name: body.student_name,
          assignment_id: 'assignment-1',
          questions_data: {
            type: 'test',
            questions: [{ question: 'What is photosynthesis?', options: ['A', 'B', 'C', 'D'], correct: 'A', difficulty: 'easy' }],
          },
          timer_seconds: 30,
        }),
      })
    } else {
      await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'Invalid session token' }) })
    }
  })
  await page.route('**/api/v1/assignments/answer', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'recorded', response_id: 'resp-new', is_correct: true }) })
  })
}

/**
 * Inject auth credentials via initScript so Pinia picks them up on first initialization.
 * Must be called before page.goto().
 */
export async function injectAuthViaInitScript(page: Page) {
  await page.addInitScript(
    ({ token, user }) => {
      localStorage.setItem('access_token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    { token: FAKE_TOKEN, user: FAKE_USER }
  )
}
