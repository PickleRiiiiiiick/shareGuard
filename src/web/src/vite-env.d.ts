/// <reference types="vite/client" />

interface ImportMetaEnv {
    PROD: boolean
    DEV: boolean
    MODE: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}