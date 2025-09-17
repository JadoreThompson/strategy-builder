import { defineConfig } from "orval";

export default defineConfig({
  app: {
    input: {
      target: "http://localhost:8000/openapi.json",
      validation: false,
      parserOptions: {
        validate: false,
      },
    },
    output: {
      target: "./src/openapi.ts",
      client: "fetch",
      override: {
        mutator: {
          path: "./src/lib/custom-fetch.ts",
          name: "customFetch",
        },
      },
    },
    hooks: { afterAllFilesWrite: "prettier --write" },
  },
});
