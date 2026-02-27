const express = require('express')
const axios = require('axios')

const router = express.Router()
const MENU_SERVICE = process.env.MENU_SERVICE_URL || 'http://menu-service:8000'

router.all('/*', async (req, res) => {
  try {
    const response = await axios({
      method: req.method,
      url: `${MENU_SERVICE}/settings${req.path}`,
      params: req.query,
      data: req.body,
      headers: { 'Content-Type': 'application/json' },
    })
    res.status(response.status).json(response.data)
  } catch (err) {
    const status = err.response?.status || 500
    res.status(status).json(err.response?.data || { error: 'Settings error' })
  }
})

module.exports = router
