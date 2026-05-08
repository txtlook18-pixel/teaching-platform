<template>
  <div class="min-h-screen bg-white">
    <!-- Navbar -->
    <nav class="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-2xl">🎓</span>
          <span class="font-bold text-gray-900 text-lg">TeachAI</span>
        </div>
        <div class="flex items-center gap-3">
          <router-link to="/login" class="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors">
            Войти
          </router-link>
          <router-link to="/register" class="btn-primary text-sm px-4 py-2">
            Регистрация
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="pt-32 pb-24 px-6 bg-gradient-to-br from-blue-50 via-indigo-50 to-white">
      <div class="max-w-4xl mx-auto text-center">
        <div class="inline-flex items-center gap-2 bg-blue-100 text-blue-700 text-sm font-medium px-4 py-1.5 rounded-full mb-8">
          <span class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
          AI-платформа нового поколения
        </div>
        <h1 class="text-5xl font-extrabold text-gray-900 leading-tight mb-6">
          Создавайте уроки<br />
          <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
            с помощью ИИ
          </span>
        </h1>
        <p class="text-xl text-gray-500 mb-10 max-w-2xl mx-auto">
          Загрузите текст, ссылку или файл — платформа сама проанализирует материал,
          сгенерирует тесты и организует интерактивный урок для ваших студентов.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <router-link to="/register" class="btn-primary text-base px-8 py-3.5 font-semibold">
            Начать бесплатно →
          </router-link>
          <router-link to="/login" class="btn-secondary text-base px-8 py-3.5 font-semibold">
            Уже есть аккаунт
          </router-link>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="py-24 px-6 bg-white">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-900 mb-4">Всё для интерактивного обучения</h2>
          <p class="text-gray-500 text-lg max-w-xl mx-auto">
            От загрузки материала до живого урока — за несколько минут
          </p>
        </div>
        <div class="grid md:grid-cols-3 gap-8">
          <div class="card hover:shadow-md transition-shadow">
            <div class="text-3xl mb-4">📄</div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">Любой источник</h3>
            <p class="text-gray-500 text-sm leading-relaxed">
              Вставьте текст вручную, укажите ссылку на сайт или загрузите PDF/DOCX файл.
              ИИ извлечёт и структурирует весь учебный материал.
            </p>
          </div>
          <div class="card hover:shadow-md transition-shadow">
            <div class="text-3xl mb-4">🤖</div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">ИИ-анализ</h3>
            <p class="text-gray-500 text-sm leading-relaxed">
              Платформа автоматически определяет темы, ключевые концепции и сложность материала.
              Генерирует вопросы трёх уровней: лёгкие, средние, сложные.
            </p>
          </div>
          <div class="card hover:shadow-md transition-shadow">
            <div class="text-3xl mb-4">⚡</div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">Живые сессии</h3>
            <p class="text-gray-500 text-sm leading-relaxed">
              Студенты присоединяются по QR-коду с телефона. Результаты обновляются
              в реальном времени прямо на экране учителя.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Activity types -->
    <section class="py-24 px-6 bg-gradient-to-br from-gray-50 to-blue-50">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-900 mb-4">5 форматов активностей</h2>
          <p class="text-gray-500 text-lg">Выберите подходящий формат для каждого урока</p>
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div v-for="item in activities" :key="item.label"
            class="bg-white rounded-2xl p-5 text-center border border-gray-100 hover:border-blue-200 hover:shadow-sm transition-all">
            <div class="text-2xl mb-2">{{ item.icon }}</div>
            <div class="font-semibold text-gray-900 text-sm">{{ item.label }}</div>
            <div class="text-xs text-gray-400 mt-1">{{ item.desc }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="py-24 px-6 bg-white">
      <div class="max-w-4xl mx-auto">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-900 mb-4">Как это работает</h2>
        </div>
        <div class="space-y-8">
          <div v-for="(step, i) in steps" :key="i" class="flex gap-6 items-start">
            <div class="flex-shrink-0 w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
              {{ i + 1 }}
            </div>
            <div>
              <h3 class="font-semibold text-gray-900 mb-1">{{ step.title }}</h3>
              <p class="text-gray-500 text-sm leading-relaxed">{{ step.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Banner -->
    <section class="py-20 px-6 bg-gradient-to-r from-blue-600 to-indigo-600">
      <div class="max-w-2xl mx-auto text-center">
        <h2 class="text-3xl font-bold text-white mb-4">Готовы начать?</h2>
        <p class="text-blue-100 text-lg mb-8">
          Регистрация бесплатна. Создайте первый урок прямо сейчас.
        </p>
        <router-link to="/register"
          class="inline-block bg-white text-blue-600 font-semibold text-base px-8 py-3.5 rounded-xl hover:bg-blue-50 transition-colors">
          Создать аккаунт →
        </router-link>
      </div>
    </section>

    <!-- Footer -->
    <footer class="py-8 px-6 bg-gray-900 text-center">
      <p class="text-gray-500 text-sm">
        © 2025 TeachAI &nbsp;·&nbsp;
        <router-link to="/login" class="hover:text-gray-300 transition-colors">Войти</router-link>
        &nbsp;·&nbsp;
        <router-link to="/register" class="hover:text-gray-300 transition-colors">Регистрация</router-link>
      </p>
    </footer>
  </div>
</template>

<script setup lang="ts">
const activities = [
  { icon: '📝', label: 'Тест', desc: 'Вопросы с выбором' },
  { icon: '⚔️', label: 'Батл', desc: 'Дискуссия в командах' },
  { icon: '🔍', label: 'Анализ', desc: 'Разбор кейсов' },
  { icon: '🃏', label: 'Карточки', desc: 'Flashcard-режим' },
  { icon: '🗣️', label: 'Пересказ', desc: 'Диалог с ИИ' },
]

const steps = [
  {
    title: 'Загрузите учебный материал',
    text: 'Вставьте текст, ссылку на статью или загрузите PDF/DOCX файл с вашим учебным контентом.',
  },
  {
    title: 'ИИ анализирует и генерирует вопросы',
    text: 'Платформа автоматически выделяет ключевые темы и создаёт вопросы разного уровня сложности.',
  },
  {
    title: 'Запустите активность',
    text: 'Выберите формат (тест, батл, карточки и др.), настройте таймер и запустите сессию.',
  },
  {
    title: 'Студенты присоединяются по QR-коду',
    text: 'Покажите QR-код на экране — студенты сканируют с телефона и сразу участвуют.',
  },
  {
    title: 'Смотрите результаты в реальном времени',
    text: 'Ответы и статистика отображаются мгновенно. После сессии — полный отчёт в архиве.',
  },
]
</script>
