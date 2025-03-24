import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
  srcDir: 'src',
  extensionApi: 'chrome',
  manifest: {
    permissions: ["activeTab"],
    action: {},
  },
  modules: ['@wxt-dev/module-svelte'],
});
