import { defineConfig } from "orval";

export default defineConfig({
  balance: {
    input: "./openapi.json",
    output: {
      target: "./src/shared/api/generated/api.ts",
      client: "fetch",
      prettier: true,
    },
  },
});
