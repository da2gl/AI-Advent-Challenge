"""Automatic analysis of temperature experiment results using Gemini API."""

import os
import sys
from datetime import datetime

from gemini_client import GeminiApiClient, GeminiModel


def analyze_experiment_results(api_key: str, prompt: str):
    """Run temperature experiment and get AI analysis of results.

    Args:
        api_key: Gemini API key
        prompt: The prompt to test with different temperatures
    """
    client = GeminiApiClient(api_key)
    temperatures = [0.0, 0.7, 1.2]

    print("=" * 80)
    print(f"TEMPERATURE EXPERIMENT WITH AI ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"\nTest Prompt: {prompt}")
    print("\n" + "=" * 80)

    # Step 1: Run experiments
    print("\nStep 1: Running experiments with different temperatures...")
    print("=" * 80)

    results = []
    for temp in temperatures:
        print(f"\nRunning with temperature = {temp}...")

        try:
            response = client.generate_content(
                prompt=prompt,
                model=GeminiModel.GEMINI_2_5_FLASH,
                temperature=temp
            )

            text = client.extract_text(response)
            usage = client.extract_usage_metadata(response)

            results.append({
                'temperature': temp,
                'response': text,
                'tokens': usage['total_tokens'] if usage else 0
            })

            print(f"✓ Temperature {temp}: {usage['total_tokens'] if usage else 0} tokens")

        except Exception as e:
            print(f"✗ Error at temperature {temp}: {str(e)}")
            results.append({
                'temperature': temp,
                'response': f"ERROR: {str(e)}",
                'tokens': 0
            })

    # Step 2: Prepare analysis prompt
    print("\n" + "=" * 80)
    print("Step 2: Asking Gemini to analyze the results...")
    print("=" * 80 + "\n")

    analysis_prompt = f"""Compare these 3 responses to the same prompt with different temperatures:

PROMPT: {prompt}

Temperature 0.0: {results[0]['response']}

Temperature 0.7: {results[1]['response']}

Temperature 1.2: {results[2]['response']}

Provide brief analysis:
1. Key differences between responses
2. Which temperature is best for what tasks
3. Main observations

Answer in markdown, be concise."""

    # Step 3: Get AI analysis
    try:
        analysis_response = client.generate_content(
            prompt=analysis_prompt,
            model=GeminiModel.GEMINI_2_5_FLASH,
            temperature=0.3,  # Low temperature for analytical task
            max_output_tokens=8192  # Increased limit for detailed analysis
        )

        # Debug: Check response structure
        if 'candidates' not in analysis_response or not analysis_response['candidates']:
            print("⚠ Warning: No candidates in analysis response")
            print(f"Response: {analysis_response}")
            analysis_text = "Error: AI did not return analysis. Response may have been blocked by safety filters."
        else:
            analysis_text = client.extract_text(analysis_response)
            if analysis_text.startswith("No content") or analysis_text.startswith("Error"):
                print("⚠ Warning: Empty or error response from AI")
                print(f"Full response: {analysis_response}")
                analysis_text = f"Error extracting analysis.\n\nFull API Response:\n```json\n{analysis_response}\n```"

        print(analysis_text)
        print("\n" + "=" * 80)

        # Step 4: Save everything to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"ai_analysis_{timestamp}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# AI Analysis of Temperature Experiment\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("**Model:** Gemini 2.5 Flash\n")
            f.write(f"**Test Prompt:** {prompt}\n\n")
            f.write("---\n\n")

            f.write("## Experiment Results\n\n")
            for result in results:
                f.write(f"### Temperature {result['temperature']}\n\n")
                f.write(f"**Tokens:** {result['tokens']}\n\n")
                f.write(f"{result['response']}\n\n")
                f.write("---\n\n")

            f.write("## AI Analysis\n\n")
            f.write(analysis_text)
            f.write("\n")

        print(f"\n✓ Full analysis saved to: {output_file}")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error during analysis: {str(e)}")

    client.close()


def main():
    """Entry point for automatic analysis."""
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment.")
        print("Please set the environment variable.")
        sys.exit(1)

    # Get prompt from command line or use default
    if len(sys.argv) > 1:
        prompt = ' '.join(sys.argv[1:])
    else:
        prompt = "Write a short story (3-4 sentences) about a robot learning to paint."
        print(f"Using default prompt: {prompt}\n")

    # Run experiment with AI analysis
    analyze_experiment_results(api_key, prompt)


if __name__ == "__main__":
    main()
