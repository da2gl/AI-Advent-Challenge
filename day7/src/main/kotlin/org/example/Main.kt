package org.example

import kotlinx.coroutines.runBlocking
import java.io.File
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

fun main() = runBlocking {
    println("╔════════════════════════════════════════════════════════════╗")
    println("║  DISASTER MOVIE GENERATOR: Two-Agent AI System            ║")
    println("║  Agent 1: Meteorologist → Agent 2: Screenwriter           ║")
    println("╚════════════════════════════════════════════════════════════╝")
    println()

    // Load API key from environment or config
    val apiKey = System.getenv("GEMINI_API_KEY")
        ?: loadApiKeyFromFile()
        ?: run {
            println("❌ Error: GEMINI_API_KEY not found!")
            println("   Please set GEMINI_API_KEY environment variable or create config.properties")
            return@runBlocking
        }

    // Test locations for disaster scenarios
    val testLocations = listOf(
        "Tokyo, Japan",
        "New York City, USA",
        "London, UK"
    )

    // User can choose location or use default
    println("Available locations for disaster scenarios:")
    testLocations.forEachIndexed { index, location ->
        println("  ${index + 1}. $location")
    }
    println("\nUsing location: ${testLocations[0]}")
    println()

    val location = testLocations[0]

    try {
        // ═══════════════════════════════════════════════════════════
        // AGENT 1: METEOROLOGIST
        // ═══════════════════════════════════════════════════════════
        println("┌────────────────────────────────────────────────────────┐")
        println("│ 🌪️  AGENT 1: METEOROLOGIST                            │")
        println("└────────────────────────────────────────────────────────┘")
        println("Analyzing weather patterns and generating disaster scenario...")
        println()

        val meteorologist = MeteorologistAgent(apiKey)
        val weatherReport = meteorologist.generateDisasterScenario(location)

        println("═══════════════════════════════════════════════════════════")
        println("  METEOROLOGICAL DISASTER REPORT")
        println("═══════════════════════════════════════════════════════════")
        println(weatherReport)
        println("═══════════════════════════════════════════════════════════")
        println()

        // Wait a moment before next agent
        println("⏳ Passing report to screenwriter agent...")
        Thread.sleep(1500)
        println()

        // ═══════════════════════════════════════════════════════════
        // AGENT 2: DISASTER SCREENWRITER
        // ═══════════════════════════════════════════════════════════
        println("┌────────────────────────────────────────────────────────┐")
        println("│ 🎬 AGENT 2: DISASTER MOVIE SCREENWRITER                │")
        println("└────────────────────────────────────────────────────────┘")
        println("Transforming weather data into blockbuster movie concept...")
        println()

        val screenwriter = DisasterScreenwriterAgent(apiKey)
        val movieScript = screenwriter.createMovieScript(weatherReport)

        println("███████████████████████████████████████████████████████████")
        println("  DISASTER MOVIE SCRIPT CONCEPT")
        println("███████████████████████████████████████████████████████████")
        println(movieScript)
        println("███████████████████████████████████████████████████████████")
        println()

        // Summary
        println("╔════════════════════════════════════════════════════════════╗")
        println("║  ✅ TWO-AGENT INTERACTION COMPLETED SUCCESSFULLY           ║")
        println("╚════════════════════════════════════════════════════════════╝")
        println()
        println("Summary:")
        println("  • Agent 1 (Meteorologist) created a disaster scenario")
        println("  • Agent 2 (Screenwriter) reviewed and transformed it into a movie")
        println("  • Data was successfully passed between agents")
        println()

        // Save results to MD file
        val resultFile = saveResultsToMarkdown(location, weatherReport, movieScript)
        println("📄 Results saved to: $resultFile")
        println()

    } catch (e: Exception) {
        println("❌ Error during execution: ${e.message}")
        e.printStackTrace()
    }
}

/**
 * Save agent results to a markdown file with timestamp
 */
private fun saveResultsToMarkdown(location: String, weatherReport: String, movieScript: String): String {
    // Create results directory if it doesn't exist
    val resultsDir = File("day7/results")
    if (!resultsDir.exists()) {
        resultsDir.mkdirs()
    }

    // Generate filename with timestamp
    val timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"))
    val filename = "result_$timestamp.md"
    val file = File(resultsDir, filename)

    // Create markdown content
    val markdown = """
# Disaster Movie Generator - Agent Interaction Result

**Generated:** ${LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}
**Location:** $location

---

## 🌪️ Agent 1: Meteorologist

### Catastrophic Weather Disaster Report

$weatherReport

---

## 🎬 Agent 2: Disaster Movie Screenwriter

### Hollywood Movie Concept

$movieScript

---

## Summary

This document shows the interaction between two AI agents:

1. **Meteorologist Agent** analyzed the location and created a catastrophic weather disaster scenario
2. **Screenwriter Agent** received the weather report and transformed it into a Hollywood disaster movie concept

The agents successfully demonstrated:
- ✅ Independent processing with different models/configurations
- ✅ Data passing from Agent 1 to Agent 2
- ✅ Agent 2 reviewing and enhancing Agent 1's output
- ✅ Text-based communication between agents

---

*Generated by Koog AI Framework with Google Gemini 2.0 Flash*
    """.trimIndent()

    // Write to file
    file.writeText(markdown)

    return file.absolutePath
}

private fun loadApiKeyFromFile(): String? {
    return try {
        val configFile = File("config.properties")
        if (configFile.exists()) {
            val properties = java.util.Properties()
            configFile.inputStream().use { properties.load(it) }
            properties.getProperty("GEMINI_API_KEY")
        } else {
            null
        }
    } catch (_: Exception) {
        null
    }
}
