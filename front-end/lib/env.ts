import { z } from "zod";

const environmentSchema = z.object({
  API_BASE_URL: z
    .url("API_BASE_URL must be a valid URL")
    .transform((url) => url.replace(/\/$/, "")),
});

export const environment = environmentSchema.parse({
  API_BASE_URL: process.env.API_BASE_URL,
});
