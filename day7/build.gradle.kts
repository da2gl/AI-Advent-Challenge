plugins {
    kotlin("jvm") version "2.2.20"
}

group = "org.example"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    // Koog AI Framework
    implementation("ai.koog:koog-agents:0.5.0")
}

kotlin {
    jvmToolchain(17)
}
