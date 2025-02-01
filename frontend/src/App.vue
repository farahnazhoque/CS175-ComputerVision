<!-- src/App.vue -->
<template>
  <div class="container">
    <div class="card">
      <h3>Upload Files</h3>
      <div class="drop_box">
        <header>
          <h4>Select File here</h4>
        </header>
        <p>Files Supported: PNG, JPG, JPEG, GIF, MOV, MP4, AVI, MKV, etc.</p>

        <!-- Actual file input, hidden by CSS, triggered by button click -->
        <input
          type="file"
          hidden
          accept=".png,.jpg,.jpeg,.gif,.mov,.mp4,.avi,.mkv"
          id="fileID"
          ref="fileInput"
          @change="onFileChange"
        />

        <!-- Button to choose file -->
        <button class="btn" @click="chooseFile">Choose File</button>

        <!-- Button to upload the chosen file -->
        <button
          v-if="selectedFileName"
          class="btn"
          style="margin-top: 10px;"
          @click="uploadFile"
        >
          Upload
        </button>

        <!-- Show selected file name -->
        <h4 v-if="selectedFileName">{{ selectedFileName }}</h4>

        <!-- Show status messages -->
        <p v-if="message" :style="{ color: error ? 'red' : 'green' }">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'App',
  setup() {
    const fileInput = ref<HTMLInputElement | null>(null)
    const selectedFile = ref<File | null>(null)
    const selectedFileName = ref<string>('')
    const message = ref<string>('')
    const error = ref<boolean>(false)

    // Trigger file dialog
    const chooseFile = () => {
      fileInput.value?.click()
    }

    // When user selects a file
    const onFileChange = (event: Event) => {
      const target = event.target as HTMLInputElement
      if (target.files && target.files[0]) {
        selectedFile.value = target.files[0]
        selectedFileName.value = target.files[0].name
      }
    }

    // Upload to Flask
    const uploadFile = async () => {
      if (!selectedFile.value) {
        message.value = 'No file selected.'
        error.value = true
        return
      }

      try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)

        // If your Flask app is running on http://127.0.0.1:5000
        const response = await fetch('http://127.0.0.1:5000/', {
          method: 'POST',
          body: formData
        })

        if (!response.ok) {
          throw new Error(`Server responded with status ${response.status}`)
        }

        const text = await response.text()
        message.value = text
        error.value = false
      } catch (err: any) {
        message.value = err.message || 'Error uploading file'
        error.value = true
      }
    }

    return {
      fileInput,
      selectedFile,
      selectedFileName,
      message,
      error,
      chooseFile,
      onFileChange,
      uploadFile
    }
  }
})
</script>

<style scoped>
.drop_box {
  margin: 20px 0;
  padding: 20px;
  border: 3px dotted #a3a3a3;
  border-radius: 5px;
  text-align: center;
}
</style>
