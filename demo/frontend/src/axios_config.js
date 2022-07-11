import axios from 'axios'
axios.defaults.withCredentials = false
export const axiosInstance = axios.create({
  method: 'get',
  // This is the url for the backend demo server launched in backend/hw.go
  baseURL: 'http://saga29.isi.edu:8081',
  timeout: 5000
})
