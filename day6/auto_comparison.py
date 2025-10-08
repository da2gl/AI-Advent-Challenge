"""Automatic comparison of direct vs step-by-step reasoning with AI analysis."""

import os
import sys
from datetime import datetime

from gemini_client import GeminiApiClient, GeminiModel


def analyze_reasoning_comparison(api_key: str, question: str):
    """Compare direct and step-by-step reasoning and get AI analysis.

    Args:
        api_key: Gemini API key
        question: The logic puzzle or problem to solve
    """
    client = GeminiApiClient(api_key)

    print("=" * 80)
    print(f"REASONING COMPARISON WITH AI ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"\nProblem: {question}")
    print("\n" + "=" * 80)

    # Step 1: Get direct answer
    print("\nStep 1: Getting direct answer (no special instructions)...")
    print("=" * 80)

    results = []

    try:
        response_direct = client.generate_content(
            prompt=question,
            model=GeminiModel.GEMINI_2_5_FLASH,
            temperature=0.7
        )

        text_direct = client.extract_text(response_direct)
        usage_direct = client.extract_usage_metadata(response_direct)

        results.append({
            'approach': 'Direct Answer',
            'prompt': question,
            'response': text_direct,
            'tokens': usage_direct['total_tokens'] if usage_direct else 0
        })

        print(f"✓ Direct answer: {usage_direct['total_tokens'] if usage_direct else 0} tokens")

    except Exception as e:
        print(f"✗ Error getting direct answer: {str(e)}")
        results.append({
            'approach': 'Direct Answer',
            'prompt': question,
            'response': f"ERROR: {str(e)}",
            'tokens': 0
        })

    # Step 2: Get step-by-step answer
    print("\n" + "=" * 80)
    print("Step 2: Getting step-by-step reasoning answer...")
    print("=" * 80)

    step_by_step_prompt = f"{question}\n\nPlease solve this step by step."

    try:
        response_steps = client.generate_content(
            prompt=step_by_step_prompt,
            model=GeminiModel.GEMINI_2_5_FLASH,
            temperature=0.7
        )

        text_steps = client.extract_text(response_steps)
        usage_steps = client.extract_usage_metadata(response_steps)

        results.append({
            'approach': 'Step-by-Step Reasoning',
            'prompt': step_by_step_prompt,
            'response': text_steps,
            'tokens': usage_steps['total_tokens'] if usage_steps else 0
        })

        print(f"✓ Step-by-step answer: {usage_steps['total_tokens'] if usage_steps else 0} tokens")

    except Exception as e:
        print(f"✗ Error getting step-by-step answer: {str(e)}")
        results.append({
            'approach': 'Step-by-Step Reasoning',
            'prompt': step_by_step_prompt,
            'response': f"ERROR: {str(e)}",
            'tokens': 0
        })

    # Step 3: Prepare analysis prompt
    print("\n" + "=" * 80)
    print("Step 3: Asking Gemini to analyze the comparison...")
    print("=" * 80 + "\n")

    analysis_prompt = f"""Compare these 2 approaches to solving the same problem:

PROBLEM: {question}

APPROACH 1 - Direct Answer (no special instructions):
{results[0]['response']}

APPROACH 2 - Step-by-Step Reasoning (with "solve step by step" instruction):
{results[1]['response']}

Provide analysis in markdown format:
1. Which answer is more correct/complete?
2. Key differences in the reasoning process
3. Pros and cons of each approach
4. When to use each approach
5. Conclusion: which approach worked better for this specific problem

Be concise but thorough."""

    # Step 4: Get AI analysis
    try:
        analysis_response = client.generate_content(
            prompt=analysis_prompt,
            model=GeminiModel.GEMINI_2_5_FLASH,
            temperature=0.3,  # Low temperature for analytical task
            max_output_tokens=8192
        )

        # Check response structure
        if 'candidates' not in analysis_response or not analysis_response['candidates']:
            print("⚠ Warning: No candidates in analysis response")
            analysis_text = "Error: AI did not return analysis. Response may have been blocked by safety filters."
        else:
            analysis_text = client.extract_text(analysis_response)
            if analysis_text.startswith("No content") or analysis_text.startswith("Error"):
                print("⚠ Warning: Empty or error response from AI")
                analysis_text = f"Error extracting analysis.\n\nFull API Response:\n```json\n{analysis_response}\n```"

        print(analysis_text)
        print("\n" + "=" * 80)

        # Step 5: Save everything to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"reasoning_comparison_{timestamp}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Direct vs Step-by-Step Reasoning Comparison\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("**Model:** Gemini 2.5 Flash\n")
            f.write(f"**Problem:** {question}\n\n")
            f.write("---\n\n")

            f.write("## Experiment Results\n\n")
            for result in results:
                f.write(f"### {result['approach']}\n\n")
                f.write(f"**Prompt:** {result['prompt']}\n\n")
                f.write(f"**Tokens:** {result['tokens']}\n\n")
                f.write(f"**Response:**\n\n{result['response']}\n\n")
                f.write("---\n\n")

            f.write("## AI Analysis\n\n")
            f.write(analysis_text)
            f.write("\n")

        print(f"\n✓ Full comparison saved to: {output_file}")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error during analysis: {str(e)}")

    client.close()


def main():
    """Entry point for automatic comparison."""
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment.")
        print("Please set the environment variable.")
        sys.exit(1)

    # Get question from command line or use default
    if len(sys.argv) > 1:
        question = ' '.join(sys.argv[1:])
    else:
        question = "Solve the equation: 3x + 7 = 2x + 15"
        print(f"Using default problem: {question}\n")

    # Run comparison with AI analysis
    analyze_reasoning_comparison(api_key, question)


if __name__ == "__main__":
    main()
