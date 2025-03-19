import { useState, useRef } from 'react'

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
const ALLOWED_TYPES = ['video/quicktime', 'video/mp4', 'video/x-msvideo']; // MOV, MP4, AVI files

export default function Upload() {
  const [file, setFile] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState('')
  const fileInputRef = useRef(null)

  const validateFile = (file) => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      setUploadStatus('Error: Please upload a MOV, MP4, or AVI file')
      return false
    }
    if (file.size > MAX_FILE_SIZE) {
      setUploadStatus('Error: File size must be less than 100MB')
      return false
    }
    return true
  }

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0]
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile)
      setUploadStatus('')
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus('Please select a file first')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      setUploadStatus('Uploading...')
      const interval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90)) // Cap at 90% until complete
      }, 500)

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      clearInterval(interval)
      setUploadProgress(100)

      let data
      try {
        data = await response.json()
      } catch {
        throw new Error('Server response was not valid JSON')
      }
      
      if (!response.ok) {
        throw new Error(data?.error || `Upload failed with status: ${response.status}`)
      }

      setUploadStatus(data.message || 'Upload successful!')
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Upload error:', error)
      setUploadStatus(`Upload failed: ${error.message}`)
    } finally {
      setUploadProgress(0)
    }
  }

  return (
    <div className="bg-white">
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              Upload Your Video
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Upload a MOV file with EXIF data to process. Maximum file size is 100MB.
            </p>
            
            <div className="mt-10 flex flex-col items-center gap-y-4">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".mov,.mp4,.avi"
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-indigo-600 file:text-white
                  hover:file:bg-indigo-500"
              />
              
              {uploadProgress > 0 && (
                <div className="w-full max-w-md bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-indigo-600 h-2.5 rounded-full"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              )}
              
              {uploadStatus && (
                <p className={`text-sm ${uploadStatus.includes('Error') ? 'text-red-500' : 'text-green-500'}`}>
                  {uploadStatus}
                </p>
              )}

              <button
                onClick={handleUpload}
                disabled={!file}
                className={`rounded-md px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm 
                  ${file ? 'bg-indigo-600 hover:bg-indigo-500' : 'bg-gray-400'} 
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600`}
              >
                Upload File
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
