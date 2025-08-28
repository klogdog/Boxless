<template>
  <div class="gmail-auth">
    <div class="card">
      <h2>Gmail API Authentication</h2>
      
      <!-- Authentication Status -->
      <div class="status-section">
        <div v-if="isAuthenticated" class="status success">
          <span class="icon">✓</span>
          <span>Connected to Gmail</span>
        </div>
        <div v-else class="status disconnected">
          <span class="icon">⚠</span>
          <span>Not connected to Gmail</span>
        </div>
      </div>

      <!-- Authentication Button -->
      <div class="auth-section">
        <button 
          v-if="!isAuthenticated"
          @click="startAuth"
          :disabled="isLoading"
          class="auth-btn primary"
        >
          <span v-if="isLoading">Connecting...</span>
          <span v-else>Connect Gmail Account</span>
        </button>
        
        <button 
          v-else
          @click="disconnect"
          class="auth-btn secondary"
        >
          Disconnect
        </button>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="error">
        <strong>Error:</strong> {{ error }}
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

        <!-- Email Test Section -->
        <div v-if="isAuthenticated" class="test-section">
          <h3>Test Gmail Access</h3>
          <div class="test-controls">
            <button @click="fetchLabels" :disabled="isLoading" class="test-btn">
              Get Labels
            </button>
            <button @click="fetchEmails" :disabled="isLoading" class="test-btn">
              Get Recent Emails
            </button>
          </div>

          <!-- Single Email Fetch -->
          <div class="single-email-section">
            <h4>Fetch Single Email</h4>
            <div class="email-input-group">
              <input 
                v-model="emailIdInput" 
                type="text" 
                placeholder="Enter email ID"
                class="email-id-input"
              >
              <button 
                @click="fetchSingleEmail" 
                :disabled="isLoading || !emailIdInput.trim()"
                class="test-btn"
              >
                Get Email
              </button>
            </div>
          </div>        <!-- Labels Display -->
        <div v-if="labels.length > 0" class="results">
          <h4>Gmail Labels:</h4>
          <div class="labels-grid">
            <span v-for="label in labels" :key="label.id" class="label-tag">
              {{ label.name }}
            </span>
          </div>
        </div>

        <!-- Emails Display -->
        <div v-if="emails.length > 0" class="results">
          <h4>Recent Emails:</h4>
          <div class="emails-list">
            <div v-for="email in emails" :key="email.id" class="email-item">
              <div class="email-subject">{{ email.subject }}</div>
              <div class="email-sender">From: {{ email.sender }}</div>
              <div class="email-date">{{ email.date }}</div>
              <div class="email-id">ID: {{ email.id }}</div>
            </div>
          </div>
        </div>

        <!-- Single Email Display -->
        <div v-if="singleEmail" class="results">
          <h4>Single Email Details:</h4>
          <div class="single-email-display">
            <div class="email-header">
              <div class="email-subject-large">{{ singleEmail.subject }}</div>
              <div class="email-meta">
                <div><strong>From:</strong> {{ singleEmail.sender }}</div>
                <div><strong>Date:</strong> {{ singleEmail.date }}</div>
                <div><strong>ID:</strong> {{ singleEmail.id }}</div>
              </div>
            </div>
            <div v-if="singleEmail.body" class="email-body">
              <h5>Body:</h5>
              <div class="email-content">{{ singleEmail.body }}</div>
            </div>
            <div v-if="singleEmail.labels && singleEmail.labels.length > 0" class="email-labels">
              <h5>Labels:</h5>
              <div class="labels-grid">
                <span v-for="label in singleEmail.labels" :key="label" class="label-tag">
                  {{ label }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Use the current host to determine API base URL
const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : 'http://127.0.0.1:8000'

// Reactive state
const isAuthenticated = ref(false)
const isLoading = ref(false)
const error = ref('')
const successMessage = ref('')
const labels = ref<Array<{id: string, name: string}>>([])
const emails = ref<Array<{id: string, subject: string, sender: string, date: string}>>([])
const emailIdInput = ref('')
const singleEmail = ref<any>(null)

// Helper function to clear messages
const clearMessages = () => {
  error.value = ''
  successMessage.value = ''
}

// Start OAuth flow
const startAuth = async () => {
  try {
    clearMessages()
    isLoading.value = true
    
    // Get authorization URL from backend
    const response = await axios.get(`${API_BASE}/gmail/auth-url`)
    const authUrl = response.data.auth_url
    
    // Open authorization URL in new window
    const authWindow = window.open(authUrl, 'gmail-auth', 'width=500,height=600')
    
    // Listen for the callback
    const checkClosed = setInterval(() => {
      if (authWindow?.closed) {
        clearInterval(checkClosed)
        // Check if authentication was successful
        checkAuthStatus()
      }
    }, 1000)
    
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to start authentication'
  } finally {
    isLoading.value = false
  }
}

// Check authentication status
const checkAuthStatus = async () => {
  try {
    // Try to fetch labels to test authentication
    await axios.get(`${API_BASE}/gmail/labels`)
    isAuthenticated.value = true
    successMessage.value = 'Successfully connected to Gmail!'
  } catch (err) {
    isAuthenticated.value = false
  }
}

// Disconnect (clear local auth state)
const disconnect = () => {
  isAuthenticated.value = false
  labels.value = []
  emails.value = []
  successMessage.value = 'Disconnected from Gmail'
}

// Fetch Gmail labels
const fetchLabels = async () => {
  try {
    clearMessages()
    isLoading.value = true
    
    const response = await axios.get(`${API_BASE}/gmail/labels`)
    labels.value = response.data.labels
    
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to fetch labels'
  } finally {
    isLoading.value = false
  }
}

// Fetch recent emails
const fetchEmails = async () => {
  try {
    clearMessages()
    isLoading.value = true
    
    const response = await axios.post(`${API_BASE}/gmail/emails`, {
      query: 'in:inbox',
      max_results: 10
    })
    emails.value = response.data
    
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to fetch emails'
  } finally {
    isLoading.value = false
  }
}

// Fetch single email by ID
const fetchSingleEmail = async () => {
  try {
    clearMessages()
    isLoading.value = true
    
    const response = await axios.get(`${API_BASE}/gmail/email/${emailIdInput.value.trim()}`)
    singleEmail.value = response.data
    successMessage.value = 'Email fetched successfully!'
    
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to fetch email'
  } finally {
    isLoading.value = false
  }
}

// Check auth status on component mount
onMounted(() => {
  checkAuthStatus()
})

// Listen for OAuth callback (if using popup)
window.addEventListener('message', (event) => {
  if (event.origin !== window.location.origin) return
  
  if (event.data.type === 'GMAIL_AUTH_SUCCESS') {
    checkAuthStatus()
  }
})
</script>

<style scoped>
.gmail-auth {
  max-width: 600px;
  margin: 0 auto;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  text-align: center;
}

.status-section {
  margin-bottom: 2rem;
}

.status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 8px;
  font-weight: 500;
}

.status.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status.disconnected {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.icon {
  font-size: 1.2rem;
}

.auth-section {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-btn {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.auth-btn.primary {
  background: #4285f4;
  color: white;
}

.auth-btn.primary:hover:not(:disabled) {
  background: #3367d6;
}

.auth-btn.secondary {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.auth-btn.secondary:hover {
  background: #e9ecef;
}

.auth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  border: 1px solid #f5c6cb;
}

.success-message {
  background: #d4edda;
  color: #155724;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  border: 1px solid #c3e6cb;
}

.test-section {
  border-top: 1px solid #dee2e6;
  padding-top: 2rem;
  margin-top: 2rem;
}

.test-section h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.test-controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.test-btn {
  padding: 0.5rem 1rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.test-btn:hover:not(:disabled) {
  background: #218838;
}

.test-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.results {
  margin-top: 1.5rem;
}

.results h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.labels-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.label-tag {
  background: #e9ecef;
  color: #495057;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.emails-list {
  max-height: 300px;
  overflow-y: auto;
}

.email-item {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 0.5rem;
  background: #f8f9fa;
}

.email-subject {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.email-sender {
  color: #6c757d;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.email-date {
  color: #6c757d;
  font-size: 0.8rem;
}

.email-id {
  color: #6c757d;
  font-size: 0.8rem;
  font-family: monospace;
  margin-top: 0.25rem;
}

.single-email-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #dee2e6;
}

.single-email-section h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.email-input-group {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.email-id-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: monospace;
}

.email-id-input:focus {
  outline: none;
  border-color: #4285f4;
  box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
}

.single-email-display {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
  background: #f8f9fa;
}

.email-header {
  margin-bottom: 1rem;
}

.email-subject-large {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.email-meta {
  color: #6c757d;
  font-size: 0.9rem;
}

.email-meta > div {
  margin-bottom: 0.25rem;
}

.email-body {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #dee2e6;
}

.email-body h5 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.email-content {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
  font-size: 0.9rem;
  line-height: 1.4;
}

.email-labels {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #dee2e6;
}

.email-labels h5 {
  margin: 0 0 0.5rem 0;
  color: #333;
}
</style>
