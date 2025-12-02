# Multi-stage Dockerfile: build with Maven, produce a lean runtime image

# Builder stage: compile the application
FROM maven:3.9.4-eclipse-temurin-17 AS builder
WORKDIR /workspace
# Copy everything. Using full copy so the Maven build sees the project.
COPY . /workspace

# Package the application (skip tests to speed up)
RUN mvn -f pom.xml -DskipTests package

# Runtime stage
FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
# Copy the fat jar produced by Spring Boot build
COPY --from=builder /workspace/target/ProxyFHIR-0.0.1-SNAPSHOT.jar /app/app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
