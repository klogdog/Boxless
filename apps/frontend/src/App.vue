<script setup lang="ts">
import GmailAuth from './components/GmailAuth.vue'
</script>

<template>
  <div id="app">
    <header>
      <h1>Boxless - Gmail API Integration</h1>
    </header>
    
    <main>
      <div class="container">
        <GmailAuth />
      </div>
    </main>
  </div>
</template>

<style scoped>
#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

header {
  padding: 2rem 0;
  text-align: center;
  color: white;
}

header h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 300;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 1rem;
}

main {
  padding: 2rem 0;
}
</style>
