import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
  srcDir: 'src',
  extensionApi: 'chrome',
  manifest: {
    permissions: ["activeTab", "tabs"],
    host_permissions: ["<all_urls>"],
    action: {},
  },
  modules: ['@wxt-dev/module-svelte'],
});
