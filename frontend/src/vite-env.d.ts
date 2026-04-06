/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_COGNITO_USER_POOL_ID: string
  readonly VITE_COGNITO_USER_POOL_CLIENT_ID: string
  readonly VITE_COGNITO_DOMAIN: string
  readonly VITE_API_ENDPOINT: string
  readonly VITE_AWS_REGION: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
