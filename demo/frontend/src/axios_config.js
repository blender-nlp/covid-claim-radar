import axios from 'axios'
axios.defaults.withCredentials = false
export const axiosInstance = axios.create({
  method: 'get',
  baseURL: 'http://18.221.187.153:8080',
  timeout: 5000
})
