<script setup lang="ts">
// No imports needed for simplified version
</script>

<template>
  <div class="welcome">
    <div class="hero">
      <h1>
        <span>Vue 3</span>
        <span>+ Turborepo</span>
      </h1>
      <p class="description">
        This is the frontend app in the Boxless monorepo.
      </p>
    </div>
    <div class="features">
      <div class="feature">
        <h3>Documentation</h3>
        <p>
          Vue’s
          <a href="https://vuejs.org/" target="_blank" rel="noopener">official documentation</a>
          provides you with all information you need to get started.
        </p>
      </div>
      <div class="feature">
        <h3>Tooling</h3>
        <p>
          This project is served and bundled with
          <a href="https://vitejs.dev/guide/features.html" target="_blank" rel="noopener">Vite</a>.
        </p>
      </div>
      <div class="feature">
        <h3>Ecosystem</h3>
        <p>
          Get official tools and libraries for your project: Pinia, VueUse, Vue I18n, Vue Router, etc.
        </p>
      </div>
      <div class="feature">
        <h3>Community</h3>
        <p>
          Get involved with other Vue users and developers on
          <a href="https://chat.vuejs.org/" target="_blank" rel="noopener">Discord</a> and
          <a href="https://github.com/vuejs/vue" target="_blank" rel="noopener">GitHub</a>.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welcome {
  width: 100%;
  max-width: 1024px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

.hero {
  margin-bottom: 4rem;
}

.hero h1 {
  font-size: 3rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.hero h1 span {
  display: block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero .description {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 2rem;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.feature {
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: border-color 0.2s;
}

.feature:hover {
  border-color: #667eea;
}

.feature h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.feature p {
  color: #666;
  line-height: 1.6;
}

.feature a {
  color: #667eea;
  text-decoration: none;
}

.feature a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .hero h1 {
    font-size: 2rem;
  }

  .features {
    grid-template-columns: 1fr;
  }
}
</style>
