const { defineConfig } = require('@vue/cli-service')

// Suppress Node.js deprecation warnings
process.removeAllListeners('warning')
process.on('warning', (warning) => {
  if (warning.name === 'DeprecationWarning' && warning.message.includes('util._extend')) {
    // Suppress util._extend deprecation warning
    return
  }
  // Show other warnings
  console.warn(warning.name, warning.message)
})

module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,  // Disable ESLint temporarily
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  productionSourceMap: false
})

