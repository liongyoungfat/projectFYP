<script setup lang="ts">
import axios from 'axios'
import { onMounted, ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'

const localhost = 'http://18.232.124.137:8000/'
const showAdd = ref(false)
const revenues = ref<Revenue[]>([])
const sortKey = ref('dateTime')
const sortOrder = ref<'asc' | 'desc'>('desc')
const isLoading = ref(false)

const sortedRevenues = computed(() => {
  const key = sortKey.value
  const order = sortOrder.value
  return [...revenues.value].sort((a, b) => {
    let aVal = a[key]
    let bVal = b[key]
    // For dateTime, sort by date
    if (key === 'dateTime') {
      aVal = new Date(aVal)
      bVal = new Date(bVal)
    }
    if (aVal < bVal) return order === 'asc' ? -1 : 1
    if (aVal > bVal) return order === 'asc' ? 1 : -1
    return 0
  })
})

const searchQuery = ref('')
const filteredRevenues = computed(() => {
  if (!searchQuery.value.trim()) return sortedRevenues.value
  const q = searchQuery.value.trim().toLowerCase()
  return sortedRevenues.value.filter((rev) => {
    return (
      formatDateKL(rev.dateTime).toLowerCase().includes(q) ||
      (rev.title && rev.title.toLowerCase().includes(q)) ||
      (rev.description && rev.description.toLowerCase().includes(q)) ||
      (rev.category && rev.category.toLowerCase().includes(q)) ||
      String(rev.amount).toLowerCase().includes(q)
    )
  })
})

function setSort(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}
const errorMessage = ref('')
const successMessage = ref('')
const isProcessing = ref(false)
const isEditMode = ref(false)

interface Revenue {
  id: number
  title: string
  description?: string
  amount: number
  category: string
  reference?: string
  file?: string
  dateTime: string
}

const defaultRevenue = {
  id: 0,
  title: 'Shopee Order',
  description: 'Order Name',
  category: 'Sales',
  amount: 0,
  reference: '',
  file: '',
  dateTime: getCurrentDateTimeString(),
}

const categories = [
  'Product Sales',
  'Service Income',
  'Commission Income',
  'Grants & Subsidies',
  'Other Income',
]

function getCurrentDateTimeString() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const newRevenue = ref({ ...defaultRevenue })
const userStore = useUserStore()
const companyId = userStore.company_id

const downloadTemplate = () => {
  window.open(localhost + 'api/template/revenue', '_blank')
}

const handleBatchUpload = async (event: Event) => {
  isLoading.value = true
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  formData.append('company_id', String(companyId))
  console.log('fDT', formData)

  try {
    await axios.post(localhost + 'api/batchUploadRevenue', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    getRevenues()
    successMessage.value = 'Batch upload successful!'
    alert(successMessage.value)
  } catch (error) {
    if (axios.isAxiosError(error) && error.response && error.response.data) {
      const msg =
        error.response.data.message ||
        error.response.data.error ||
        `Registration failed. (${error.response.status})`
      alert(msg)
    } else {
      alert('Something went wrong.')
    }
  } finally {
    isLoading.value = false
  }
}

const getRevenues = async () => {
  try {
    const response = await axios.get(localhost + 'api/revenues', {
      params: { company_id: companyId },
    })
    revenues.value = response.data
  } catch (error) {
    console.error('Error fetching revenues:', error)
  }
}

const formValid = computed(() => {
  return (
    newRevenue.value.amount > 0 &&
    newRevenue.value.dateTime !== '' &&
    newRevenue.value.category !== '' &&
    newRevenue.value.title !== ''
  )
})

const triggerFileInput = () => {
  const input = document.getElementById('fileInput')
  if (input) {
    input.click()
  }
}

const triggerBatchUpload = () => {
  const input = document.getElementById('batchRevenue') as HTMLInputElement
  if (input) {
    input.click()
  } else {
    isLoading.value = false
  }
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) uploadFile(file)
}

const uploadFile = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  console.log(file)
  isProcessing.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const uploadResponse = await axios.post(localhost + 'api/uploadFile?type=revenue', formData, {
      headers: {
        'Content-Type': 'multipart/form-data', // Explicit header
      },
    })
    console.log('Extracted data:', uploadResponse.data.path)
    const s3Key = uploadResponse.data.s3_key
    // 2. Process file with Gemini
    const processResponse = await axios.post(localhost + 'api/processReceipt', {
      type: 'revenue',
      s3_key: s3Key,
    })
    console.log('Gemini response:', processResponse.data)
    if (processResponse.data.result) {
      const resultString = processResponse.data.result
      const jsonString = resultString
        .replace(/```json/g, '')
        .replace(/```/g, '')
        .trim()
      const extractedData = JSON.parse(jsonString)

      console.log('Parsed data:', extractedData)
      newRevenue.value = {
        ...newRevenue.value,
        dateTime: extractedData.dateTime,
        title: extractedData.title,
        category: extractedData.category || 'Meals',
        amount: extractedData.amount,
      }
      console.log('pm', newRevenue.value.title)
      successMessage.value =
        'Receipt processed successfully! Please review the extracted data before submit.'
      return extractedData
    } else if (processResponse.data.excel_data) {
      // This is an array of summary objects (from backend)
      const summaryArray = processResponse.data.excel_data
      const revenueObj = summaryArray.find((row: any) => row.label === 'Total Revenue')
      if (revenueObj) {
        newRevenue.value.amount = revenueObj.amount
        successMessage.value = 'Excel processed! Please review and fill in other fields if needed.'
        return revenueObj
      } else {
        errorMessage.value = 'Could not find Total Revenue in Excel file.'
      }
    }
  } catch (error) {
    if (axios.isAxiosError(error) && error.response && error.response.data) {
      const msg =
        error.response.data.message ||
        error.response.data.error ||
        `Failed to process file. (${error.response.status})`
      alert(msg)
    } else {
      alert('Something went wrong.')
    }
  } finally {
    isProcessing.value = false
  }
}

const handleSubmit = async () => {
  if (isEditMode.value) {
    await submitEditRevenue()
  } else {
    await addRevenue()
  }
}

const addRevenue = async () => {
  console.log('addrevenue')
  try {
    const payload = { ...newRevenue.value, company_id: companyId }
    const response = await axios.post(localhost + 'api/createRevenue', payload)
    console.log(response.data)
    revenues.value.push(response.data)
    showAdd.value = false
    alert('Revenue added successfully!')
    getRevenues()
  } catch (error) {
    console.error('Error adding revenue:', error)
  }
}

const openEditModal = async (revenue: Revenue) => {
  isEditMode.value = true
  const date = new Date(revenue.dateTime)
  const formattedDateTime = date.toISOString().slice(0, 16)
  newRevenue.value = {
    ...revenue,
    description: revenue.description ?? '',
    reference: revenue.reference ?? '',
    file: revenue.file ?? '',
    dateTime: formattedDateTime,
  } // spread to copy fields, ensure no undefined
  showAdd.value = true // or your modal flag
}

const submitEditRevenue = async () => {
  console.log('Submitting edit for:', newRevenue.value)
  try {
    const response = await axios.post(localhost + 'api/updateRevenue', newRevenue.value)
    console.log('Updated revenue:', response.data)

    getRevenues()
    showAdd.value = false
    isEditMode.value = false
    successMessage.value = 'Revenue updated successfully!'
    alert(successMessage.value)
  } catch (error) {
    console.error('Error updating revenue:', error)
    errorMessage.value = 'Failed to update revenue. Please try again later.'
  }
}

const deleteRevenue = async (id: number) => {
  if (!confirm('Are you sure you want to delete this revenue record?')) return
  try {
    await axios.post(localhost + `api/deleteRevenue`, { id: id })
    revenues.value = revenues.value.filter((rev) => rev.id !== id)
    successMessage.value = 'Revenue deleted successfully!'
    alert(successMessage.value)
  } catch (error) {
    console.error('Error deleting revenue:', error)
    errorMessage.value = 'Failed to delete revenue. Please try again later.'
  }
}

function formatDateKL(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleString('en-GB', {
    timeZone: 'UTC',
    weekday: 'short', // "Thu"
    day: '2-digit', // "17"
    month: 'short', // "Jul"
    year: 'numeric', // "2025"
    hour: '2-digit', // "16"
    minute: '2-digit', // "01"
    second: '2-digit', // "00"
    hour12: false,
  })
}

onMounted(async () => {
  try {
    getRevenues()
  } catch (error) {
    console.error('API Error:', error)
  }
})
</script>

<template>
  <div class="main-content">
    <div class="header-row">
      <h2 class="header-title">💹 Revenue Management</h2>
      <div class="button-group">
        <button @click="downloadTemplate" class="header-btn">Download Template</button>
        <input type="file" id="batchRevenue" hidden @change="handleBatchUpload" />
        <button
          @click="triggerBatchUpload"
          class="header-btn"
          :disabled="isLoading"
          :style="isLoading ? 'opacity:0.6;cursor:not-allowed;' : ''"
        >
          <span v-if="isLoading">Processing...</span>
          <span v-else>Batch Upload</span>
        </button>
        <button @click="showAdd = !showAdd" class="header-btn primary-btn">
          {{ showAdd ? 'Cancel' : '+ New Revenue' }}
        </button>
      </div>
    </div>

    <div class="expenses-container">
      <div v-if="revenues.length" class="expenses-container">
        <div class="expenses-card">
          <div class="expenses-title-row">
            <h3 class="expenses-title">Revenues Table</h3>
            <div class="search-bar-container">
              <input
                v-model="searchQuery"
                type="text"
                class="search-bar"
                placeholder="Search by date, title, description, category, or amount..."
                :title="'Search by date, title, description, category, or amount...'"
              />
            </div>
          </div>
          <div class="table-container">
            <table class="expenses-table fixed-table">
              <thead>
                <tr>
                  <th style="width: 16.66%; cursor: pointer" @click="setSort('dateTime')">
                    Date Time
                    <span v-if="sortKey === 'dateTime'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
                  </th>
                  <th style="width: 16.66%; cursor: pointer" @click="setSort('title')">
                    Title
                    <span v-if="sortKey === 'title'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
                  </th>
                  <th style="width: 16.66%; cursor: pointer" @click="setSort('description')">
                    Description
                    <span v-if="sortKey === 'description'">{{
                      sortOrder === 'asc' ? '▲' : '▼'
                    }}</span>
                  </th>
                  <th style="width: 16.66%; cursor: pointer" @click="setSort('category')">
                    Category
                    <span v-if="sortKey === 'category'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
                  </th>
                  <th style="width: 16.66%; cursor: pointer" @click="setSort('amount')">
                    Amount
                    <span v-if="sortKey === 'amount'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
                  </th>
                  <th style="width: 16.66%">Action</th>
                </tr>
              </thead>
            </table>
            <div class="table-scroll-body">
              <table class="expenses-table">
                <tbody>
                  <tr v-for="rev in filteredRevenues" :key="rev.id">
                    <td style="width: 16.66%">{{ formatDateKL(rev.dateTime) }}</td>
                    <td style="width: 16.66%">{{ rev.title }}</td>
                    <td style="width: 16.66%">{{ rev.description }}</td>
                    <td style="width: 16.66%">{{ rev.category }}</td>
                    <td style="width: 16.66%">{{ rev.amount }}</td>
                    <td style="width: 16.66%">
                      <button @click="openEditModal(rev)" class="edit-button">Edit</button>
                      <button @click="deleteRevenue(rev.id)" class="delete-button">Delete</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state attractive-empty">
        <div class="empty-icon bounce">
          <svg width="80" height="80" fill="none" viewBox="0 0 80 80">
            <rect x="12" y="28" width="56" height="36" rx="10" fill="#e0e7ef" />
            <rect x="22" y="38" width="36" height="6" rx="3" fill="#a5b4fc" />
            <rect x="22" y="50" width="24" height="6" rx="3" fill="#fca311" />
            <rect x="22" y="62" width="16" height="6" rx="3" fill="#34d399" />
            <circle cx="40" cy="22" r="10" fill="#f1f5f9" stroke="#6366f1" stroke-width="3" />
            <path d="M40 16v12M34 22h12" stroke="#6366f1" stroke-width="3" stroke-linecap="round" />
            <circle cx="40" cy="22" r="3" fill="#6366f1" />
            <path d="M40 70c8 0 16-4 16-10H24c0 6 8 10 16 10z" fill="#e0e7ef" />
          </svg>
        </div>
        <div class="empty-message">
          <h3 class="gradient-text">No revenues found</h3>
          <p class="fade-in">
            Start by adding a new revenue to see it here.<br />
            <span class="tip"
              >Tip: Try the <b>Batch Upload according to template</b> for faster entry!</span
            >
          </p>
        </div>
      </div>
    </div>
  </div>

  <div v-if="showAdd" class="modal-overlay" @click.self="showAdd = false">
    <div class="modal-content">
      <!-- <h2>{{ isEditMode ? 'Edit Revenue' : 'Add New Revenue' }}</h2> -->
      <div class="content-container">
        <div class="upload-section attractive-upload">
          <h2 class="modal-gradient-title">
            {{ isEditMode ? 'Edit Revenue' : 'Create New Revenue' }}
          </h2>
          <div class="modal-gradient-subtitle">
            Upload Receipt <span class="auto-fill">for auto fill</span>
          </div>
          <input
            type="file"
            id="fileInput"
            accept=".pdf,.jpg,.jpeg,.png"
            hidden
            @change="handleFileUpload"
          />
          <button
            class="upload-btn attractive-upload-btn"
            @click="triggerFileInput"
            :disabled="isProcessing"
            :style="isProcessing ? 'opacity:0.6;cursor:not-allowed;' : ''"
          >
            <span class="upload-icon">📁</span>
            <span class="upload-text">
              {{ isProcessing ? 'Processing...' : 'Choose File' }}
            </span>
          </button>
          <div v-if="successMessage && !isProcessing" class="ai-reminder">
            <span class="reminder-icon">💡</span>
            <span class="reminder-text">
              <b>Reminder:</b> Please
              <span style="color: #2563eb; font-weight: 600">review and confirm</span> all
              auto-filled fields before submitting.<br />
              <span style="color: #64748b; font-size: 0.97em"
                >AI extraction may not be 100% accurate.</span
              >
            </span>
          </div>
        </div>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>Date and Time:</label>
          <input type="datetime-local" v-model="newRevenue.dateTime" required />
        </div>

        <div class="form-group">
          <label>Title:</label>
          <input v-model="newRevenue.title" required />
        </div>

        <div class="form-group">
          <label>Description:</label>
          <input v-model="newRevenue.description" />
        </div>

        <div class="form-group">
          <label>Category:</label>
          <select v-model="newRevenue.category" required>
            <option v-for="cat in categories" :value="cat" :key="cat">
              {{ cat }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Amount (RM):</label>
          <input type="number" v-model.number="newRevenue.amount" min="0.01" step="0.01" required />
        </div>

        <div class="form-actions">
          <button
            type="button"
            @click="((showAdd = false), (isEditMode = false), (successMessage = ''))"
            class="cancel-btn"
          >
            Cancel
          </button>
          <button type="submit" :disabled="!formValid" class="submit-btn">
            {{ isEditMode ? 'Save Changes' : 'Save Revenue' }}
          </button>
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.upload-section.attractive-upload {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.upload-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 2px;
}
.upload-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #6366f1;
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  border: none;
  border-radius: 10px;
  padding: 12px 24px;
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.13);
  cursor: pointer;
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}

.attractive-upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #6366f1;
  color: #fff;
  font-weight: 600;
  font-size: 0.875rem;
  border: none;
  border-radius: 10px;
  padding: 8px 20px;
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.13);
  cursor: pointer;
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}

.upload-btn.attractive-upload-btn:hover {
  background: #4338ca;
  color: #fca311;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.18);
}
.upload-btn.attractive-upload-btn:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.18);
}
.upload-icon {
  font-size: 1.3rem;
  margin-right: 2px;
}
.upload-text {
  font-size: 1rem;
  font-weight: 600;
}
.modal-gradient-title {
  width: 100%;
  text-align: center;
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 2px;
  background: linear-gradient(90deg, #6366f1 0%, #fca311 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.modal-gradient-subtitle {
  width: 100%;
  text-align: center;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 5px;
  background: linear-gradient(90deg, #6366f1 0%, #fca311 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auto-fill {
  color: #fca311;
  font-weight: 700;
}

.container {
  display: flex;
  min-height: 100vh;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #2c3e50;
}

.button-group {
  display: flex;
  gap: 12px;
}

.header-btn {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 8px;
  background-color: #e2e8f0;
  color: #1e293b;
  cursor: pointer;
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.09);
}
.header-btn:hover {
  background-color: #cbd5e1;
  color: #2563eb;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(59, 130, 246, 0.18);
}
.header-btn:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.18);
}
.primary-btn {
  background-color: #2563eb;
  color: white;
  font-weight: 700;
}
.primary-btn:hover {
  background-color: #1d4ed8;
  color: #fff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.18);
}
.primary-btn:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.18);
}

.expenses-container {
  width: 100%;
  max-height: 78vh;
  background-color: #f9fafb;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f6f9fc;
  position: relative;
}

.table-container {
  width: 100%;
  height: 80%;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.expenses-card {
  width: 90%;
  background-color: #fff;
  max-height: 720px;
  border-radius: 10px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.expenses-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 10px;
  text-align: left;
}

.expenses-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  align-items: center;
  text-align: center;
}

/* Title and search bar on same row */
.expenses-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.search-bar-container {
  margin-bottom: 0;
  display: flex;
  justify-content: flex-end;
  flex: 1;
  width: auto;
}
.search-bar {
  width: 50%;
  min-width: 320px;
  padding: 10px 16px;
  border-radius: 8px;
  border: 1.5px solid #d1d5db;
  font-size: 15px;
  color: #222;
  background: #f9fafb;
  transition:
    border-color 0.18s,
    box-shadow 0.18s;
  box-shadow: 0 1px 4px rgba(59, 130, 246, 0.04);
}
.search-bar:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.13);
  background-color: #f0f7ff;
}

.table-scroll-body {
  max-height: 370px;
  overflow-y: auto;
  overflow-x: hidden;
}

.scrollable-tbody tr {
  display: table;
  width: 100%;
  table-layout: fixed;
}

thead,
.scrollable-tbody {
  width: 100%;
}

thead tr {
  display: table;
  width: 100%;
  table-layout: fixed;
}

.expenses-table th,
.expenses-table td {
  padding: 12px 16px;
  text-align: center;
  border-bottom: 1px solid #eee;
}

.expenses-table th {
  background-color: #f4f6f8;
  font-weight: 600;
  color: #333;
}

.edit-button,
.delete-button {
  padding: 6px 12px;
  border: none;
  border-radius: 5px;
  font-size: 14px;
  cursor: pointer;
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}

.edit-button {
  background-color: #eaeaea;
  color: #333;
  margin-right: 6px;
}
.edit-button:hover {
  background-color: #cbd5e1;
  color: #2563eb;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(59, 130, 246, 0.18);
}
.edit-button:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.18);
}

.delete-button {
  background-color: #e74c3c;
  color: white;
}
.delete-button:hover {
  background-color: #c0392b;
  color: #fff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(231, 76, 60, 0.18);
}
.delete-button:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.18);
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.loading {
  padding: 20px;
  text-align: center;
  color: #7f8c8d;
}

.main-content {
  padding: 20px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: #f8fafc; /* match tax page background */
  border-radius: 12px; /* same rounded corners */
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04); /* softer shadow */
  margin-bottom: 20px;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b; /* match tax title text color */
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.button-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-btn {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 8px;
  background-color: #e2e8f0;
  color: #1e293b;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.header-btn:hover {
  background-color: #cbd5e1;
}

.primary-btn {
  background-color: #2563eb;
  color: white;
}

.primary-btn:hover {
  background-color: #1d4ed8;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  transition: opacity 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  color: black;
  padding: 30px;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 10px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #2c3e50;
  font-weight: 500;
}

input,
select {
  width: 100%;
  padding: 10px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-size: 16px;
}

input:focus,
select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.form-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.cancel-btn {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.09);
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}
.cancel-btn:hover {
  background: #c0392b;
  color: #fff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(231, 76, 60, 0.18);
}
.cancel-btn:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.18);
}

.submit-btn {
  background: #2ecc71;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  flex: 2;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(46, 204, 113, 0.09);
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}
.submit-btn:hover:enabled {
  background: #27ae60;
  color: #fff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(46, 204, 113, 0.18);
}
.submit-btn:active:enabled {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(46, 204, 113, 0.18);
}

.submit-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.error-message {
  color: #e74c3c;
  margin-top: 15px;
  text-align: center;
}

.processing-message {
  color: #6366f1;
  font-weight: 700;
  text-align: center;
  margin-bottom: 12px;
  font-size: 1.1rem;
}
.ai-reminder {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #eef2ff;
  color: #6366f1;
  border-radius: 8px;
  padding: 10px 16px;
  margin: 12px 0 18px 0;
  font-size: 1rem;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.07);
}
.reminder-icon {
  font-size: 1.3rem;
  margin-top: 2px;
}
.reminder-text {
  flex: 1;
}

.button-group {
  display: flex;
  gap: 10px;
}

.fixed-table {
  table-layout: fixed;
}
.fixed-table th,
.fixed-table td {
  width: 16.66%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 480px) {
  .modal-content {
    width: 95%;
    padding: 20px;
  }

  .form-actions {
    flex-direction: column;
  }

  .cancel-btn,
  .submit-btn {
    flex: auto;
    width: 100%;
  }
}

/* --- Custom Empty State Styles --- */
.attractive-empty {
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ef 100%);
  border-radius: 18px;
  box-shadow: 0 6px 32px rgba(99, 102, 241, 0.08);
  min-height: 320px;
  max-width: 600px;
  width: 100%;
  padding: 60px 0 40px 0;
  position: fixed;
  top: 50%;
  left: 60%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
.bounce {
  animation: bounce 1.6s infinite cubic-bezier(0.28, 0.84, 0.42, 1);
}
@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-18px);
  }
}
.gradient-text {
  background: linear-gradient(90deg, #6366f1 0%, #fca311 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 10px;
  text-align: center;
}
.fade-in {
  animation: fadeIn 1.2s;
}
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.tip {
  display: inline-block;
  margin-top: 8px;
  font-size: 0.98rem;
  color: #6366f1;
  background: #eef2ff;
  border-radius: 6px;
  padding: 2px 10px;
  font-weight: 500;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0 40px 0;
  color: #64748b;
}
.empty-icon {
  margin-bottom: 18px;
}
.empty-message h3 {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: #334155;
  text-align: center;
}
.empty-message p {
  font-size: 1rem;
  color: #64748b;
  text-align: center;
}
</style>
