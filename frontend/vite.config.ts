/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import mdx from '@mdx-js/rollup'
import remarkFrontmatter from 'remark-frontmatter'
import remarkMdxFrontmatter from 'remark-mdx-frontmatter'
import remarkGfm from 'remark-gfm'

export default defineConfig({
  plugins: [
    mdx({
      remarkPlugins: [remarkFrontmatter, remarkMdxFrontmatter, remarkGfm],
    }),
    react(),
  ],
  server: {
    allowedHosts: true,
  },
  build: {
    rolldownOptions: {
      output: {
        manualChunks(id) {
          // Let recharts + d3 stay in the lazy-loaded Dashboard chunk
          // so they are NOT modulepreload-ed on every page
          if (id.includes('node_modules/@radix-ui')) {
            return 'radix-ui'
          }
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'cobertura'],
    },
  },
})
