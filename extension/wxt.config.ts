import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
  srcDir: 'src',
  extensionApi: 'chrome',
  manifest: {
    permissions: ["activeTab"],
    action: {},
  },
  runner: {
    chromiumProfile: "/home/office/.config/google-chrome/Default"
  },
  modules: ['@wxt-dev/module-svelte'],
});
