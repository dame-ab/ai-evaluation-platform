#! /usr/bin/env bash
# Regenerate frontend/src/client from the backend's current OpenAPI schema.
# Run this after changing any backend route, model, or schema.

set -e
set -x

cd backend
FASTAPI_ENV=development python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > ../frontend/openapi.json
cd ../frontend
npm run generate-client
npx biome check --write --unsafe --no-errors-on-unmatched --files-ignore-unknown=true ./
