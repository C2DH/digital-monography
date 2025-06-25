import { defineConfig } from "cypress";

export default defineConfig({
  env: {
    ...process.env,
  },

  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});
