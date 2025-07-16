<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios, { AxiosError } from 'axios'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id
const userId = userStore.user_id

interface Expense {
  id: number
  dateTime: string
  payment_method: string
  user_id: number
  category: string
  amount: number
  company_id?: number
}

const expenses = ref<Expense[]>([])
const showModal = ref(false)
const showEditModal = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const isDragging = ref(false)
const ocrProcessing = ref(false)
const receiptPreview = ref(null)
const isProcessing = ref(false)


const defaultExpense = {
  id: 0,
  dateTime: getCurrentDateTimeString(),
  payment_method: 'Online banking',
  user_id: userId,
  category: 'Meals',
  amount: 0,
  company_id: companyId,
}

function getCurrentDateTimeString() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const newExpense = ref({ ...defaultExpense })

const paymentMethods = ['Online Banking', 'Credit Card', 'Debit Card', 'eWallet', 'Cash', 'Other']

const categories = [
  'Meals',
  'Transportation',
  'Entertainment',
  'Travel',
  'Office Supplies',
  'Marketing',
  'Utilities',
  'Software',
]

const localhost = 'http://localhost:5000/'

const getExpenses = async () => {
  try {
    const res = await axios.get(localhost + 'api/expenses', {
      params: { company_id: companyId },
    })
    expenses.value = res.data as Expense[]
    console.log('expenses val', expenses.value)
  } catch (error) {
    console.error('Failed to load expenses:', error)
  }
}

const formValid = computed(() => {
  return (
    newExpense.value.amount > 0 &&
    newExpense.value.dateTime !== '' &&
    newExpense.value.category !== '' &&
    newExpense.value.payment_method !== ''
  )
})

const resetForm = () => {
  newExpense.value = { ...defaultExpense }
  errorMessage.value = ''
}

const downloadTemplate = () => {
  window.open(localhost + 'api/template/expenses', '_blank')
}

const handleBatchUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  formData.append('company_id', String(companyId!))
  formData.append('user_id', String(userId!))
  console.log('formData', formData)

  try {
    await axios.post(localhost + 'api/batchUploadExpenses', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    getExpenses()
    alert('Batch upload successful!')
    successMessage.value = 'Batch upload successful!'
  } catch (err) {
    console.log('err in line 101', err)
    errorMessage.value = 'Batch upload failed'
  }
}

const triggerFileInput = () => {
  const input = document.getElementById('fileInput')
  if (input) {
    input.click()
  }
}

const triggerBatchFileInput = () => {
  const input = document.getElementById('batchFile') as HTMLInputElement | null
  if (input) {
    input.click()
  }
}

// Update existing methods to use uploadFile
const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) uploadFile(file)
}

const handleDragOver = () => {
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (e: DragEvent) => {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  console.log(file)
  if (file) uploadFile(file)
}

// Add this method to handle file uploads
const uploadFile = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  console.log(file)
  isProcessing.value= true
  try {
    const uploadResponse = await axios.post(localhost + 'api/uploadFile?type=expense', formData, {
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
      let dataToUse = extractedData
      if (Array.isArray(extractedData)) {
        if (extractedData.length === 0) {
          errorMessage.value = 'No data extracted from receipt.'
          return
        }
        // Optionally, you could prompt user to select, but for now use the first
        dataToUse = extractedData[0]
        successMessage.value = 'Multiple receipts found. Only the first one is used.'
      }
      if (dataToUse.category == 'Food' || dataToUse.category == 'food') {
        dataToUse.category = 'Meals'
      }
      if (
        dataToUse.payment_method == null ||
        dataToUse.payment_method == 'not found' ||
        !paymentMethods.includes(dataToUse.payment_method)
      ) {
        errorMessage.value = 'Payment method is ' + dataToUse.payment_method
      }
      dataToUse.payment_method = dataToUse.payment_method ? dataToUse.payment_method.toLowerCase() : ''
      newExpense.value = {
        ...newExpense.value,
        dateTime: dataToUse.dateTime,
        payment_method: dataToUse.payment_method,
        category: dataToUse.category || 'Meals',
        amount: dataToUse.amount,
      }
      console.log('pm', newExpense.value)
      successMessage.value =
        'Receipt processed successfully! Please review the extracted data before submit.'
      return dataToUse
    } else if (processResponse.data.excel_data) {
      // This is an array of summary objects (from backend)
      const summaryArray = processResponse.data.excel_data
      const revenueObj = summaryArray.find((row) => row.label === 'Total Expenses')
      if (revenueObj) {
        newExpense.value.amount = revenueObj.amount
        // You can set other fields as needed, or display to user for manual review
        successMessage.value = 'Excel processed! Please review and fill in other fields if needed.'
        return revenueObj
      } else {
        errorMessage.value = 'Could not find Total Expenses in Excel file.'
      }
    }
  } catch (error) {
    console.error('Upload failed:', error)
    errorMessage.value = 'Failed to process receipt. Please try it later.'
  }finally{
    isProcessing.value=false
  }
}

const submitExpense = async () => {
  try {
    isLoading.value = true
    showModal.value = false
    const response = await axios.post(localhost + 'api/createExpenses', {
      dateTime: newExpense.value.dateTime,
      payment_method: newExpense.value.payment_method.toLowerCase(),
      user_id: newExpense.value.user_id,
      category: newExpense.value.category,
      amount: parseFloat(newExpense.value.amount.toFixed(2)),
      company_id: newExpense.value.company_id || companyId,
    })
    expenses.value = [response.data, ...expenses.value]
    resetForm()
    alert('Expense saved!')
    getExpenses()
  } catch (error) {
    errorMessage.value = 'Failed to save expense. Please try again.'
    console.error('Submission Error:', error)
  } finally {
    isLoading.value = false
  }
}

const editExpenses = async (expense: Expense) => {
  const date = new Date(expense.dateTime)
  const formattedDateTime = date.toISOString().slice(0, 16)
  newExpense.value = { ...expense, dateTime: formattedDateTime, company_id: companyId }
  showEditModal.value = true
}

const updateExpense = async () => {
  console.log('Updating expense:', newExpense.value)
  try {
    const res = await axios.post(localhost + 'api/updateExpenses', {
      ...newExpense.value,
      payment_method: newExpense.value.payment_method.toLowerCase(),
      amount: parseFloat(newExpense.value.amount.toFixed(2)),
    })
    console.log('res', res)
    showEditModal.value = false
    alert('Update Successfully!!')
    getExpenses()
  } catch (error) {
    console.log('newexp', newExpense.value)
    console.error('Update failed:', error)
  }
}

const deleteExpense = async (expenseId: number) => {
  if (!confirm('Are you sure you want to delete this expense?')) return

  try {
    const response = await axios.post(localhost + 'api/deleteExpenses', {
      id: expenseId,
    })

    if (response.data.message === 'Expense deleted successfully') {
      expenses.value = expenses.value.filter((exp) => exp.id !== expenseId)
    }
  } catch (error) {
    // Handle AxiosError type
    const axiosError = error as AxiosError

    console.error('Delete failed:', axiosError.response?.data || axiosError.message)

    alert('Delete failed: ' + axiosError.message)
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
    second: '2-digit',
  })
}

onMounted(async () => {
  try {
    getExpenses()
    console.log('expenses value', expenses.value)
  } catch (error) {
    console.error('API Error:', error)
  }
})
</script>

<template>
  <main class="main-content">
    <div class="header-row">
      <h2 class="header-title">💸📋Expenses Management</h2>
      <div class="button-group">
        <button @click="downloadTemplate" class="header-btn">Download Template</button>
        <input type="file" id="batchFile" hidden @change="handleBatchUpload" />
        <button @click="triggerBatchFileInput" class="header-btn">Batch Upload</button>
        <button @click="showModal = true" class="header-btn primary-btn">+ New Expense</button>
      </div>
    </div>
    <div class="expenses-container">
      <div v-if="expenses.length" class="expenses-container">
        <div class="expenses-card">
          <h3 class="expenses-title">Expenses Table</h3>
          <div class="table-container">
            <table class="expenses-table">
              <thead>
                <tr>
                  <th style="width: 16.66%">No</th>
                  <th style="width: 16.66%">Date</th>
                  <th style="width: 16.66%">Payment Method</th>
                  <th style="width: 16.66%">Category</th>
                  <th style="width: 16.66%">Amount (RM)</th>
                  <th style="width: 16.66%">Action</th>
                </tr>
              </thead>
            </table>
            <div class="table-scroll-body">
              <table class="expenses-table">
                <tbody>
                  <tr v-for="(expense, idx) in expenses" :key="expense.id">
                    <td style="width: 16.66%">{{ idx + 1 }}</td>
                    <td style="width: 16.66%">{{ formatDate(expense.dateTime) }}</td>
                    <td style="width: 16.66%">{{ expense.payment_method }}</td>
                    <td style="width: 16.66%">{{ expense.category }}</td>
                    <td style="width: 16.66%">{{ expense.amount.toFixed(2) }}</td>
                    <td style="width: 16.66%">
                      <button @click="editExpenses(expense)" class="edit-button">Edit</button>
                      <button @click="deleteExpense(expense.id)" class="delete-button">
                        Delete
                      </button>
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
          <h3 class="gradient-text">No expenses found</h3>
          <p class="fade-in">
            Start by adding a new expense to see it here.<br />
            <span class="tip"
              >Tip: Try the <b>Batch Upload according to template</b> for faster entry!</span
            >
          </p>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content">
        <h2 class="modal-title-gradient">Create New Expense</h2>
        <div class="content-container">
          <div class="upload-section">
            <div
              class="upload-area"
              :class="{ dragover: isDragging }"
              @dragover.prevent="handleDragOver"
              @dragleave="handleDragLeave"
              @drop.prevent="handleDrop"
            >
              <i class="fas fa-file-upload upload-icon"></i>
              <h3 class="upload-title-gradient">
                Upload Receipt for <span style="color: #fca311; font-weight: 700">auto fill</span>
              </h3>
              <input
                type="file"
                id="fileInput"
                accept=".pdf,.jpg,.jpeg,.png"
                hidden
                @change="handleFileUpload"
              />

              <button
                class="upload-btn"
                @click="triggerFileInput"
                :disabled="isProcessing"
                :style="isProcessing ? 'opacity:0.6;cursor:not-allowed;' : ''"
              >
                📁
                <span class="upload-text">
                  {{ isProcessing ? 'Processing...' : 'Choose File' }}
                </span>
              </button>
              <div v-if="successMessage" class="ai-reminder">
                <span>
                  <b>Reminder:</b> Please
                  <span style="color: #2563eb; font-weight: 600">review and confirm</span> all
                  auto-filled fields before submitting. AI extraction may not be 100% accurate.
                </span>
              </div>
            </div>
          </div>
        </div>

        <form @submit.prevent="submitExpense">
          <div class="form-group">
            <label>Date and Time:</label>
            <input type="datetime-local" v-model="newExpense.dateTime" required />
          </div>
          <div class="form-group">
            <label>Payment Method:</label>
            <select v-model="newExpense.payment_method" required>
              <option
                v-for="method in paymentMethods"
                :value="method.toLowerCase()"
                :key="method.toLowerCase()"
              >
                {{ method }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Category:</label>
            <select v-model="newExpense.category" required>
              <option v-for="cat in categories" :value="cat" :key="cat">
                {{ cat }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Amount (RM):</label>
            <input
              type="number"
              v-model.number="newExpense.amount"
              min="0.01"
              step="0.01"
              required
            />
          </div>

          <div class="form-actions">
            <button type="button" @click="showModal = false" class="cancel-btn">Cancel</button>
            <button type="submit" :disabled="!formValid || isLoading" class="submit-btn">
              {{ isLoading ? 'Saving...' : 'Create Expense' }}
            </button>
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
        </form>
      </div>
    </div>

    <div v-if="showEditModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content">
        <h2>Update Expense</h2>
        <form @submit.prevent="updateExpense">
          <div class="form-group">
            <label>Date and Time:</label>
            {{ newExpense.dateTime }}
            <input type="datetime-local" v-model="newExpense.dateTime" required />
          </div>

          <div class="form-group">
            <label>Payment Method:</label>
            <select v-model="newExpense.payment_method" required>
              <option
                v-for="method in paymentMethods"
                :value="method.toLowerCase()"
                :key="method.toLowerCase()"
              >
                {{ method }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Category:</label>
            <select v-model="newExpense.category" required>
              <option v-for="cat in categories" :value="cat" :key="cat">
                {{ cat }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Amount (RM):</label>
            <input
              type="number"
              v-model.number="newExpense.amount"
              min="0.01"
              step="0.01"
              required
            />
          </div>

          <div class="receipt-preview" v-if="receiptPreview">
            <p>Receipt Preview:</p>
            <img :src="receiptPreview" alt="Receipt preview" />
          </div>

          <div v-if="ocrProcessing" class="ocr-status">
            <div class="processing-animation">
              <div class="spinner"></div>
              <span>Processing receipt and extracting data...</span>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" @click="showEditModal = false" class="cancel-btn">Cancel</button>
            <button type="submit" :disabled="!formValid || isLoading" class="submit-btn">
              {{ isLoading ? 'Saving...' : 'Edit Expense' }}
            </button>
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
          <div v-if="successMessage" class="ocr-status">
            <i class="fas fa-check-circle"></i> {{ successMessage }}
          </div>
        </form>
      </div>
    </div>
  </main>
</template>

<style scoped>
.expenses-container {
  width: 100%;
  max-height: 80vh;
  background-color: #f9fafb;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f6f9fc;
}

.table-container {
  width: 100%;
  height: 80%;
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

.expense-table {
  background-color: #ffffff;
  width: 100%;
  max-width: 1100px;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow-x: auto;
}

.expense-table table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

.expense-table th,
.expense-table td {
  padding: 14px 18px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  text-align: center;
}

.expense-table th {
  background-color: #f3f4f6;
  color: #374151;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 13px;
}

.expense-table tr:hover {
  background-color: #f9fafc;
}

button {
  padding: 6px 14px;
  font-size: 13px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  background-color: #f1f1f1;
  color: #333;
  transition: background-color 0.2s ease;
}

button:hover {
  background-color: #e0e0e0;
}

.cancel-btn {
  background-color: #e74c3c;
  color: #fff;
}

.cancel-btn:hover {
  background-color: #c0392b;
}

.loading {
  padding: 40px;
  font-size: 18px;
  color: #7f8c8d;
  text-align: center;
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
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}
.submit-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
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

.error-message {
  color: #e74c3c;
  margin-top: 15px;
  text-align: center;
}

.upload-btn {
  background-color: #4f46e5; /* Indigo */
  color: #ffffff;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background-color 0.3s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  will-change: transform, box-shadow;
}
.upload-btn:hover {
  background-color: #4338ca; /* Darker Indigo */
  color: #fff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(79, 70, 229, 0.18);
}
.upload-btn:active {
  background-color: #3730a3; /* Even darker on click */
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.18);
}
.upload-btn i {
  font-size: 16px;
  transition: transform 0.18s;
}

/* Responsive */
@media (max-width: 768px) {
  .expense-table {
    padding: 20px;
  }

  .expense-table th,
  .expense-table td {
    padding: 10px;
    font-size: 12px;
  }

  button {
    padding: 6px 10px;
    font-size: 12px;
  }
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
  margin: 0 auto;
  min-height: 320px;
  width: 100%;
  max-width: 600px;
  padding: 60px 0 40px 0;
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
/* Attractive modal title */
.modal-title-gradient {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 18px;
  background: linear-gradient(90deg, #6366f1 0%, #fca311 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center;
}
/* Attractive upload title */
.upload-title-gradient {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 10px;
  background: linear-gradient(90deg, #2563eb 0%, #fca311 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center;
  letter-spacing: 0.5px;
}
</style>
