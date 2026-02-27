import axios from 'axios'

export const menuApi = axios.create({ baseURL: '/api' })
export const orderApi = axios.create({ baseURL: '/orders-api' })
