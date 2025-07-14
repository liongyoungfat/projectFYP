<script setup lang="ts">
import axios from 'axios'
import { onMounted, ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'

const localhost = 'http://localhost:5000/'
const showAdd = ref(false)
const revenues = ref<Revenue[]>([])
const errorMessage = ref('')
const successMessage = ref('')
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
  } catch (err) {
    errorMessage.value = `Batch upload failed, ${err}`
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

  try {
    const uploadResponse = await axios.post(localhost + 'api/uploadFile?type=revenue', formData, {
      headers: {
        'Content-Type': 'multipart/form-data', // Explicit header
      },
    })
    console.log('Extracted data:', uploadResponse.data.path)
    const filePath = uploadResponse.data.path
    // 2. Process file with Gemini
    const processResponse = await axios.post(localhost + 'api/processReceipt', {
      file_path: filePath,
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
      extractedData.payment_method = extractedData.payment_method.toLowerCase()
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
    console.error('Upload failed:', error)
    errorMessage.value = 'Failed to process receipt. Please try it later.'
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
  } catch (error) {
    console.error('Error deleting revenue:', error)
    errorMessage.value = 'Failed to delete revenue. Please try again later.'
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('en-GB', {
    timeZone: 'Asia/Kuala_Lumpur',
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
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
        <button @click="triggerBatchUpload" class="header-btn">Batch Upload</button>
        <button @click="showAdd = !showAdd" class="header-btn primary-btn">
          {{ showAdd ? 'Cancel' : '+ New Revenue' }}
        </button>
      </div>
    </div>

    <div class="expenses-container">
      <div v-if="revenues.length" class="expenses-container">
        <div class="expenses-card">
          <h3 class="expenses-title">Revenues Table</h3>
          <div class="table-container">
            <table class="expenses-table fixed-table">
              <thead>
                <tr>
                  <th style="width: 16.66%">Date Time</th>
                  <th style="width: 16.66%">Title</th>
                  <th style="width: 16.66%">Description</th>
                  <th style="width: 16.66%">Category</th>
                  <th style="width: 16.66%">Amount</th>
                  <th style="width: 16.66%">Action</th>
                </tr>
              </thead>
            </table>
            <div class="table-scroll-body">
              <table class="expenses-table">
                <tbody>
                  <tr v-for="rev in revenues" :key="rev.id">
                    <td style="width: 16.66%">{{ formatDate(rev.dateTime) }}</td>
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
      <div v-else class="loading">Loading revenues...</div>
    </div>
  </div>

  <div v-if="showAdd" class="modal-overlay" @click.self="showAdd = false">
    <div class="modal-content">
      <h2>{{ isEditMode ? 'Edit Revenue' : 'Input New Revenue' }}</h2>
      <div class="content-container">
        <div class="upload-section">
          <div class="upload-area">
            <i class="fas fa-file-upload upload-icon"></i>
            <h3>Upload Receipt</h3>
            <input
              type="file"
              id="fileInput"
              accept=".pdf,.jpg,.jpeg,.png"
              hidden
              @change="handleFileUpload"
            />
            <button class="upload-btn" @click="triggerFileInput">
              Choose File
            </button>
          </div>
        </div>
      </div>

      <form @submit.prevent="handleSubmit">
        {{ isEditMode ? 'Edit Revenue' : 'Add New Revenue' }}
        <div class="form-group">
          <label>Date and Time:</label>
          <input type="datetime-local" v-model="newRevenue.dateTime" required />
        </div>

        <div class="form-group">
          <label>Title:</label>
          <input v-model="newRevenue.title" required />
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
          <button type="button" @click="showAdd = false" class="cancel-btn">Cancel</button>
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
  padding: 10px 18px;
  border: none;
  border-radius: 4px;
  background-color: #cddce0;
  color: #2c3e50;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.header-btn:hover {
  background-color: #adb2b9;
}

.primary-btn {
  background-color: #3498db;
  color: white;
}

.primary-btn:hover {
  background-color: #2980b9;
}

.expenses-container {
  width: 100%;
  max-height: 78vh;
  background-color: #f9fafb;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f6f9fc;
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
  max-height: 80%;
  border-radius: 10px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.expenses-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  text-align: left;
}

.expenses-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  align-items: center;
  text-align: center;
}

.table-scroll-body {
  max-height: 430px;
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
}

.edit-button {
  background-color: #eaeaea;
  color: #333;
  margin-right: 6px;
}

.delete-button {
  background-color: #e74c3c;
  color: white;
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
  margin-bottom: 24px;
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
  margin-bottom: 20px;
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
}

.submit-btn {
  background: #2ecc71;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  flex: 2;
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
</style>
