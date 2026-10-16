# O Maven gera as classes Java diretamente do contrato compartilhado.
FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY proto proto
COPY sources/weather sources/weather
RUN mvn -B -f sources/weather/pom.xml package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/sources/weather/target/weather-0.1.0.jar /app/weather.jar
ENTRYPOINT ["java", "-jar", "/app/weather.jar"]
