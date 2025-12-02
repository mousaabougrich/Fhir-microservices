# ProxyFHIR

This repository implements a FHIR proxy/interoperability layer. It ingests FHIR NDJSON exports (Synthea-generated or other bulk exports), saves resources in a PostgreSQL database, exposes REST endpoints to read and search resources, and provides a bulk-export-like file-serving API so downstream systems can fetch the original NDJSON files.

This README documents the architecture, how to build and run the project (including Docker Compose), configuration options (including how to change how many patients Synthea generates), the available HTTP endpoints, testing examples, and troubleshooting tips.

---

## What this proxy does (high-level)

- Reads bulk FHIR NDJSON files (Synthea output) from a configured directory.
- Imports each JSON object into a `fhir_resource` table (one row per resource) and stores the original JSON text in a `content` column.
- Exposes REST endpoints to:
  - Query and retrieve stored resources (by type, by id, by patient reference, etc.).
  - Provide statistics about imported resources.
  - Serve the original NDJSON files via `/bulk` endpoints (manifest, files, resource-type streams).
- Provides a POST `/fhir` endpoint to ingest a FHIR Bundle or single resource directly.

This makes the service usable as a test proxy for downstream systems (they can call `/bulk` endpoints to download NDJSON files or call the API to query resources).

---

## Repo structure (important files)

- `docker-compose.yml` - Compose setup for `db`, `synthea` (generator), and `app` (this service).
- `Dockerfile.runtime` - runtime Dockerfile that uses the built JAR in `target/`.
- `synthea-sample/` - contains `generate.sh`, the Synthea JAR and sample generated folders (e.g. `100-patients`).
- `src/main/java/.../controller/` - REST controllers (endpoints).
- `src/main/java/.../importer/SyntheaImporterRunner.java` - CommandLineRunner that imports `.ndjson` files from a configured directory.
- `src/main/java/.../model/FhirResource.java` - JPA entity for storing resources (the `content` field stores raw JSON text).

---

## Prerequisites

- Docker and Docker Compose (Docker Desktop on Windows suggested).
- Java & Maven only needed if you want to rebuild the JAR locally. On Windows use the bundled wrapper `mvnw.cmd`.
- (Optional) curl or a REST client to test endpoints.

---

## Configuration and environment

- The Compose setup maps the PostgreSQL container's `5432` to host `5433` (so host Postgres tools should connect to `localhost:5433`). Inside the Compose network the application connects to the DB at hostname `db:5432`.

- You can configure how many patients Synthea should generate via the `NUM_PATIENTS` environment variable. Default is controlled in `.env` (created in this repo) and in `docker-compose.yml`. Example `.env`:

```text
NUM_PATIENTS=10
```

- `docker-compose.yml` starts three services:
  - `db` (Postgres 15) — mapped to host port 5433
  - `synthea` (runs `synthea-sample/generate.sh {NUM_PATIENTS}` inside a JRE image)
  - `app` (this service, built from `Dockerfile.runtime` using prebuilt JAR in `target/`)

- Application properties (important ones):
  - `--synthea.files.dir` and `--synthea.import.dir` — point both the export controller and the importer to the generated Synthea folder; in Compose we pass `--synthea.files.dir=/synthea/${NUM_PATIENTS}-patients` and `--synthea.import.dir=/synthea/${NUM_PATIENTS}-patients` so both use the same folder.

---

## How to build (local development)

If you want to compile the Java project locally and produce the JAR used by `Dockerfile.runtime`:

From repo root on Windows (cmd.exe):

```cmd
mvnw.cmd -DskipTests package
```

This produces `target/ProxyFHIR-0.0.1-SNAPSHOT.jar`.

If you don't want to build locally, the repo already contains `target/ProxyFHIR-0.0.1-SNAPSHOT.jar` — Docker will use that when building the `app` image via `Dockerfile.runtime`.

---

## How to run with Docker Compose (recommended for reproducible runs)

1. Ensure `.env` contains the desired `NUM_PATIENTS` value (or set it on the command line):

```cmd
set NUM_PATIENTS=10
```

2. Start the compose stack (build the runtime image will copy the local JAR from `target/`):

```cmd
docker compose up --build
```

Notes:
- `synthea` service will run `sh /synthea/generate.sh ${NUM_PATIENTS}` and create a folder like `synthea-sample/10-patients` (inside the repo via the mounted volume).
- `app` service waits for that folder to exist, then starts and imports `.ndjson` files from that folder (importer runner). The import will insert rows into the Postgres DB.
- Host Postgres is reachable on `localhost:5433` (container listens on `5432` internally).

Detach run:

```cmd
docker compose up --build -d
```

Check logs:

```cmd
docker compose logs -f app
docker compose logs -f synthea
docker compose logs -f db
```

---

## Endpoints and examples (API surface)

Base application port: `http://localhost:8080`

1) Bulk file endpoints (serve NDJSON files)

- GET /bulk/manifest
  - Returns a JSON manifest listing NDJSON files found in the configured `synthea.files.dir`.
  - Example:

```cmd
curl http://localhost:8080/bulk/manifest
```

- GET /bulk/files/{filename}
  - Streams the raw `.ndjson` file content. Example:

```cmd
curl http://localhost:8080/bulk/files/Patient.000.ndjson -v
```

- GET /bulk/resource/{resourceType}
  - Streams all NDJSON files for that resource type (useful to fetch all `Condition` files). Example:

```cmd
curl http://localhost:8080/bulk/resource/Condition -v
```

2) Generic FHIR ingestion & listing endpoints (`/fhir`)

- POST /fhir
  - Ingest a FHIR Bundle or a single resource (raw JSON text in body). Returns a generated numeric id.
  - Example:

```cmd
curl -X POST -H "Content-Type: application/json" --data @someResource.json http://localhost:8080/fhir
```

- GET /fhir
  - Lists all rows in the `fhir_resource` table (useful to see imports).

- GET /fhir/{id}
  - Get a stored resource by numeric DB id.

- GET /fhir/type/{resourceType}
  - Get all stored rows for a given resource type (e.g., Patient, Condition).

- GET /fhir/health
  - Simple health check; reports total stored rows.

3) Resource-type focused API (`/api/fhir`)

These endpoints are resource-aware and return FHIR-style Bundle searchsets.

- GET /api/fhir/Patient
- GET /api/fhir/Patient/{id}
- GET /api/fhir/Condition
- GET /api/fhir/Condition/{id}
- GET /api/fhir/Observation
- GET /api/fhir/Observation/{id}
- GET /api/fhir/Encounter
- GET /api/fhir/Encounter/{id}
- GET /api/fhir/Procedure
- GET /api/fhir/Procedure/{id}
- GET /api/fhir/MedicationRequest
- GET /api/fhir/MedicationRequest/{id}
- GET /api/fhir/DiagnosticReport
- GET /api/fhir/DiagnosticReport/{id}
- GET /api/fhir/DocumentReference
- GET /api/fhir/DocumentReference/{id}
- GET /api/fhir/Immunization
- GET /api/fhir/Immunization/{id}
- GET /api/fhir/Device
- GET /api/fhir/Device/{id}
- GET /api/fhir/Location
- GET /api/fhir/Location/{id}
- GET /api/fhir/Organization
- GET /api/fhir/Organization/{id}
- GET /api/fhir/Practitioner
- GET /api/fhir/Practitioner/{id}
- GET /api/fhir/PractitionerRole
- GET /api/fhir/PractitionerRole/{id}

Paging and filtering:
- Endpoints accept `page` and `size` query params.
- Endpoints for some types accept `patient` to filter by `Patient/{id}` reference.

Example: list first 50 conditions for patient `096e15b5-e013-9b8c-f664-9bda8843f048`:

```cmd
curl "http://localhost:8080/api/fhir/Condition?patient=096e15b5-e013-9b8c-f664-9bda8843f048&size=50"
```

4) Statistics

- GET /api/fhir/stats
  - Returns counts by resource type and total.

---

## Why the `content` field previously looked like a quoted string

- The original import stored JSON as text in the DB. When the API serialized the `content` property as a regular string, JSON serialization escaped inner quotes so the HTTP output looked like `"{...}"`.
- To fix this, the `FhirResource` model exposes `content` with `@JsonRawValue`, which tells Jackson to emit the stored string as raw JSON (so the response contains the JSON object rather than a quoted, escaped string).
- Note: older rows in the DB that contain already-escaped JSON text will still appear escaped until re-imported or cleaned.

---

## Typical workflow / recommended steps

1. Build the JAR if you plan to use local build instead of prebuilt `target/`:

```cmd
mvnw.cmd -DskipTests package
```

2. Configure `NUM_PATIENTS` (via `.env` or the environment). Example to generate 100 patients:

```cmd
set NUM_PATIENTS=100
docker compose up --build
```

3. Wait for logs: `synthea` will generate the `/synthea/<N>-patients` folder inside `synthea-sample`. The `app` waits for that folder then imports `.ndjson` files.

4. Check the importer logs (app logs):

```cmd
docker compose logs -f app
```

You should see lines like `Importing file Patient.000.ndjson` and `Imported X resources from Patient.000.ndjson`.

5. Test endpoints as shown above.

---

## Testing tips and quick checks

- If `/bulk/manifest` returns 400: check the `filesDir` configured and ensure the expected folder exists (the app uses `--synthea.files.dir` default or whatever is passed as a command line property). When running compose we pass `--synthea.files.dir=/synthea/${NUM_PATIENTS}-patients`.

- If the app fails to connect to Postgres at startup with `UnknownHostException: db`: ensure you're running via `docker compose` so the `db` service is available on the internal network. When you run the app outside Docker you'll need to set `SPRING_DATASOURCE_URL` to `jdbc:postgresql://localhost:5433/proxyfhir` or run Postgres on `db` host.

- If API responses show `content` as a quoted string (escaped JSON): either re-import the data or normalize DB rows so `content` stores the raw JSON (unescaped). New imports done by the current importer will store `content` as raw JSON strings and the API returns them as JSON objects.

---

## Git and ignoring generated files

To avoid committing generated patient folders or the Synthea JAR, add patterns to `.gitignore` (already suggested earlier). Example rules to add to `.gitignore`:

```
# Ignore Synthea output and JAR
*-patients/
*.jar
/target/
```

If files were already tracked, stop tracking them (example commands):

```cmd
# Untrack generated dirs and jars
git rm -r --cached "synthea-sample/*-patients" "*.jar"
# Add/commit .gitignore
git add .gitignore
git commit -m "Stop tracking generated patient folders and jars"
```

Be mindful on Windows about CRLF/LF normalization. See `.gitattributes` or `core.autocrlf` settings if you get warnings.

---

## Notes about model training (ModelRisque)

- The `ModelRisque` you described (XGBoost + SHAP) needs sufficiently many labeled examples to train reliably. The synthetic datasets from Synthea are helpful but are synthetic — treat model performance estimates accordingly.
- Rules of thumb: for a fairly stable small model you typically want hundreds to thousands of patients. Of your candidate numbers (100, 400, 500):
  - 100 patients is small — likely insufficient to learn robust clinical patterns.
  - 400–500 is better; prefer 500+ if possible.
  - If you can easily generate more (1k, 5k, 10k) do so — more training data gives better model generalization.

---

## Troubleshooting common errors

1. Docker build fails pulling Maven or base images:
   - Some older tags may be removed from Docker Hub; update `Dockerfile`/Compose to use available tags (e.g., `maven:3.10.1-openjdk-17` or `eclipse-temurin:17-jre`). The runtime `Dockerfile.runtime` already uses `eclipse-temurin:17-jre-jammy`.

2. `UnknownHostException: db` / App can't connect to DB:
   - Ensure you used `docker compose up` (Docker Compose sets up the internal network and service hostnames).
   - If you run app outside Docker, set `SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5433/proxyfhir` and ensure Postgres is running on host port 5433.

3. `/bulk/manifest` returns `files directory not found`:
   - Confirm path passed to the app (`--synthea.files.dir`) matches the mounted path where Synthea wrote files. When running with Compose and the `synthea` service from this repo, the generated folder will appear as `./synthea-sample/<N>-patients` and the app accesses it at `/synthea/<N>-patients` inside the container.

4. `content` shows as escaped JSON:
   - Older DB rows might contain escaped JSON. Re-run importer to re-insert rows or update DB cells to unescape the JSON content.

---

## Next steps and improvements

- Add tests that exercise the importer and controllers (unit + integration).
- Provide an endpoint to trigger import on-demand (currently import runs at application startup via `SyntheaImporterRunner`).
- Improve search/filtering performance by indexing frequently queried JSON fields or using a JSONB column and Postgres JSON queries.
- Add authentication/authorization if exposing in a real environment.

---

If you'd like, I can:
- Add a small `README` section showing PowerShell/cmd-specific curl examples.
- Add a `Makefile` or Windows `.bat` to run the build-and-run sequence.
- Update `docker-compose.yml` to use alternate Maven/runtime tags if image pulls are failing for you.

File created: `README.md` in repo root.

