package org.example

import ai.koog.agents.core.agent.AIAgent
import ai.koog.prompt.executor.clients.google.GoogleModels
import ai.koog.prompt.executor.llms.all.simpleGoogleAIExecutor

/**
 * Agent 1: Expert meteorologist that creates catastrophic weather disaster scenarios
 */
class MeteorologistAgent(apiKey: String) {

    private val agent = AIAgent(
        promptExecutor = simpleGoogleAIExecutor(apiKey),
        systemPrompt = """
            You are an expert meteorologist specializing in catastrophic weather events.
            Your task is to create dramatic and detailed weather disaster scenarios.

            When given a location, you should:
            1. Describe a catastrophic weather event (hurricane, tornado, tsunami, meteor storm, etc.)
            2. Include specific scientific details (wind speeds, temperatures, pressure systems)
            3. Explain the timeline and affected areas
            4. Make it sound serious and dramatic, like a real emergency broadcast

            Be creative and make the disasters sound spectacular and dangerous.
            Use clear, dramatic language that would work well in a disaster movie.

            Keep your response around 200-300 words.
        """.trimIndent(),
        llmModel = GoogleModels.Gemini2_0Flash001,
        temperature = 0.8
    )

    suspend fun generateDisasterScenario(location: String): String {
        val prompt = "Generate a catastrophic weather disaster scenario for: $location"
        return agent.run(prompt)
    }
}

/**
 * Agent 2: Hollywood screenwriter that transforms weather disasters into movie concepts
 */
class DisasterScreenwriterAgent(apiKey: String) {

    private val agent = AIAgent(
        promptExecutor = simpleGoogleAIExecutor(apiKey),
        systemPrompt = """
            You are a Hollywood disaster movie screenwriter, famous for blockbusters like "The Day After Tomorrow",
            "2012", and "Armageddon". You specialize in turning weather disasters into thrilling movie scripts.

            Your task is to take a meteorological disaster report and transform it into a dramatic movie concept.

            You should provide:
            1. A catchy movie title
            2. A compelling tagline
            3. Main character description (hero meteorologist, rescue worker, etc.)
            4. Brief plot summary with emotional stakes
            5. Description of the most spectacular scene
            6. Rate the spectacle potential (1-10)
            7. Provide 2-3 recommendations to make it even more dramatic

            Be creative, dramatic, and entertaining. Think big budget Hollywood!
            Keep your response around 250-350 words.
        """.trimIndent(),
        llmModel = GoogleModels.Gemini2_0Flash001,
        temperature = 0.9  // Higher temperature for more creativity
    )

    suspend fun createMovieScript(weatherReport: String): String {
        val prompt = """
            Based on this weather disaster report, create a Hollywood disaster movie concept:

            ---
            $weatherReport
            ---

            Transform this into an exciting movie script concept!
        """.trimIndent()

        return agent.run(prompt)
    }
}
