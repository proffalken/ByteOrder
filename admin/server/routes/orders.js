const express = require('express')
const axios = require('axios')

const router = express.Router()
const ORDER_SERVICE = process.env.ORDER_SERVICE_URL || 'http://order-service:8001'

router.all('/*', async (req, res) => {
  try {
    const response = await axios({
      method: req.method,
      url: `${ORDER_SERVICE}/orders${req.path}`,
      params: req.query,
      data: req.body,
      headers: { 'Content-Type': 'application/json' },
    })
    res.status(response.status).json(response.data)
  } catch (err) {
    const status = err.response?.status || 500
    res.status(status).json(err.response?.data || { error: 'Order service error' })
  }
})

module.exports = router
