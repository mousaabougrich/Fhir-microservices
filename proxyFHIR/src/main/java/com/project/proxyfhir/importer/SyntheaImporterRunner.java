package com.project.proxyfhir.importer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.project.proxyfhir.model.FhirResource;
import com.project.proxyfhir.repository.FhirResourceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Component
@Order(Ordered.LOWEST_PRECEDENCE)
public class SyntheaImporterRunner implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(SyntheaImporterRunner.class);
    private final FhirResourceRepository repository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${synthea.import.dir:}")
    private String importDir;

    public SyntheaImporterRunner(FhirResourceRepository repository) {
        this.repository = repository;
    }

    @Override
    public void run(String... args) throws Exception {
        if (importDir == null || importDir.isBlank()) {
            log.info("Synthea importer: no import directory configured (set synthea.import.dir). Skipping.");
            return;
        }

        Path dir = Paths.get(importDir);
        if (!Files.exists(dir) || !Files.isDirectory(dir)) {
            log.warn("Synthea importer: configured path '{}' does not exist or is not a directory. Skipping.", importDir);
            return;
        }

        log.info("Synthea importer: scanning directory '{}' for .ndjson files", importDir);

        List<Path> ndjsonFiles;
        try (Stream<Path> stream = Files.list(dir)) {
            ndjsonFiles = stream.filter(p -> p.toString().toLowerCase().endsWith(".ndjson"))
                    .collect(Collectors.toList());
        }

        if (ndjsonFiles.isEmpty()) {
            log.info("Synthea importer: no .ndjson files found in '{}'", importDir);
            return;
        }

        int totalImported = 0;
        for (Path f : ndjsonFiles) {
            log.info("Importing file {}", f.getFileName());
            int imported = importNdjsonFile(f);
            totalImported += imported;
            log.info("Imported {} resources from {}", imported, f.getFileName());
            // after successful import move the file into an imported/ subfolder so we don't re-import on restart
            try {
                Path importedDir = dir.resolve("imported");
                if (!Files.exists(importedDir)) Files.createDirectory(importedDir);
                Path target = importedDir.resolve(f.getFileName());
                Files.move(f, target);
                log.info("Moved imported file {} -> {}", f.getFileName(), target.toString());
            } catch (IOException e) {
                log.warn("Failed to move imported file {}: {}", f.getFileName(), e.getMessage());
            }
            // brief pause to yield CPU and reduce DB pressure between files
            try { Thread.sleep(250); } catch (InterruptedException ignored) {}
        }

        log.info("Synthea importer: completed. Total resources imported: {}", totalImported);
    }

    private int importNdjsonFile(Path file) {
        int count = 0;
        List<FhirResource> batch = new ArrayList<>();
        final int BATCH_SIZE = 1000;
        try {
            String content = Files.readString(file, StandardCharsets.UTF_8);
            List<String> jsonObjects = splitJsonObjects(content);

            // Fallback to line-based parsing if no objects found
            if (jsonObjects.isEmpty()) {
                try (BufferedReader reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        line = line.trim();
                        if (line.isEmpty()) continue;
                        jsonObjects.add(line);
                    }
                }
            }

            for (String obj : jsonObjects) {
                if (obj == null || obj.isBlank()) continue;
                try {
                    JsonNode node = objectMapper.readTree(obj);
                    if (!node.has("resourceType")) {
                        log.debug("Skipping JSON without resourceType: {}", obj);
                        continue;
                    }
                    String resourceType = node.get("resourceType").asText();
                    String resourceId = node.has("id") ? node.get("id").asText() : null;

                    FhirResource res = new FhirResource(resourceType, resourceId, obj);
                    batch.add(res);
                    count++;

                    if (batch.size() >= BATCH_SIZE) {
                        repository.saveAll(batch);
                        batch.clear();
                        // small pause to allow DB to catch up
                        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
                    }
                } catch (IOException e) {
                    log.warn("Failed to parse JSON object in {}: {}", file.getFileName(), e.getMessage());
                }
            }

            if (!batch.isEmpty()) {
                repository.saveAll(batch);
            }

        } catch (IOException e) {
            log.error("Failed to read file {}: {}", file.toString(), e.getMessage());
        }

        return count;
    }

    /**
     * Splits a String that may contain one or more JSON objects (possibly pretty-printed / multi-line)
     * into individual JSON object strings by scanning for balanced braces while being aware of strings
     * and escape characters.
     */
    private List<String> splitJsonObjects(String s) {
        List<String> out = new ArrayList<>();
        if (s == null || s.isBlank()) return out;

        StringBuilder sb = new StringBuilder();
        boolean inString = false;
        boolean escape = false;
        int depth = 0;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            sb.append(c);

            if (escape) {
                escape = false;
                continue;
            }
            if (c == '\\') {
                escape = true;
                continue;
            }
            if (c == '"') {
                inString = !inString;
                continue;
            }
            if (!inString) {
                if (c == '{') {
                    depth++;
                } else if (c == '}') {
                    depth--;
                    if (depth == 0) {
                        String obj = sb.toString().trim();
                        if (!obj.isBlank()) out.add(obj);
                        sb.setLength(0);
                    }
                }
            }
        }

        return out;
    }
}
