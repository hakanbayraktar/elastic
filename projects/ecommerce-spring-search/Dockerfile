# Stage 1: Build JAR with Maven
FROM maven:3.9-eclipse-temurin-21-alpine AS builder
WORKDIR /build
COPY adapter/pom.xml .
COPY adapter/src ./src
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /build/target/product-search-adapter-*.jar app.jar
EXPOSE 8080
ENV SERVER_ADDRESS=0.0.0.0
ENV SERVER_PORT=8080
ENV ELASTICSEARCH_URL=http://elasticsearch:9200
ENTRYPOINT ["java", "-jar", "app.jar"]
