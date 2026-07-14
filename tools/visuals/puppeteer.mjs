import { createRequire } from 'node:module'

const require = createRequire(new URL('../../studio-kit/pipeline/generators/package.json', import.meta.url))
const puppeteer = require('puppeteer')

export default puppeteer.default ?? puppeteer
