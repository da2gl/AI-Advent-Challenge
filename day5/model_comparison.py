"""Compare different AI models on the same prompt."""

import os
from datetime import datetime
from typing import List, Dict
from huggingface_client import HuggingFaceClient, HuggingFaceModel
from groq_client import GroqClient, GroqModel


class ModelComparison:
    """Compare multiple AI models on the same prompt."""

    def __init__(self):
        """Initialize API clients."""
        # Get API keys from environment variables
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        if not self.hf_api_key:
            raise ValueError("HUGGINGFACE_API_KEY environment variable not set")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        # Initialize clients
        self.hf_client = HuggingFaceClient(self.hf_api_key)
        self.groq_client = GroqClient(self.groq_api_key)

    def run_comparison(self, prompt: str) -> List[Dict]:
        """Run the same prompt on all models and collect results.

        Args:
            prompt: The prompt to test on all models

        Returns:
            List of dictionaries with model results
        """
        results = []

        print(f"Testing prompt: '{prompt}'\n")
        print("=" * 80)

        # Model 1: HuggingFace Arch-Router-1.5B (WORST)
        print("\n1. Testing katanemo/Arch-Router-1.5B (1.5B params)...")
        try:
            result1 = self.hf_client.generate_text(
                prompt=prompt,
                model=HuggingFaceModel.ARCH_ROUTER_1_5B
            )
            result1["provider"] = "HuggingFace Inference API"
            result1["size"] = "1.5B"
            result1["rank"] = "Worst (smallest)"
            results.append(result1)
            print(f"✓ Response received in {result1['time_seconds']}s")
        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({
                "model": HuggingFaceModel.ARCH_ROUTER_1_5B,
                "provider": "HuggingFace Inference API",
                "size": "1.5B",
                "rank": "Worst (smallest)",
                "error": str(e)
            })

        # Model 2: HuggingFace SmolLM3-3B (MEDIUM)
        print("\n2. Testing HuggingFaceTB/SmolLM3-3B (3B params)...")
        try:
            result2 = self.hf_client.generate_text(
                prompt=prompt,
                model=HuggingFaceModel.SMOLLM3_3B
            )
            result2["provider"] = "HuggingFace Inference API"
            result2["size"] = "3B"
            result2["rank"] = "Medium"
            results.append(result2)
            print(f"✓ Response received in {result2['time_seconds']}s")
        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({
                "model": HuggingFaceModel.SMOLLM3_3B,
                "provider": "HuggingFace Inference API",
                "size": "3B",
                "rank": "Medium",
                "error": str(e)
            })

        # Model 3: Groq Llama-3.1-8B (BEST)
        print("\n3. Testing llama-3.1-8b-instant (8B params)...")
        try:
            result3 = self.groq_client.generate_text(
                prompt=prompt,
                model=GroqModel.LLAMA_3_1_8B
            )
            result3["provider"] = "Groq API"
            result3["size"] = "8B"
            result3["rank"] = "Best (largest)"
            results.append(result3)
            print(f"✓ Response received in {result3['time_seconds']}s")
        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({
                "model": GroqModel.LLAMA_3_1_8B,
                "provider": "Groq API",
                "size": "8B",
                "rank": "Best (largest)",
                "error": str(e)
            })

        print("\n" + "=" * 80)
        return results

    def generate_report(self, prompt: str, results: List[Dict]) -> str:
        """Generate a markdown report with comparison results.

        Args:
            prompt: The prompt that was tested
            results: List of model results

        Returns:
            Markdown formatted report
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# AI Model Comparison Report

**Generated:** {timestamp}

## Test Configuration

**Prompt:** "{prompt}"

**Models Tested:**
1. **Worst:** katanemo/Arch-Router-1.5B (1.5B params) - HuggingFace
2. **Medium:** HuggingFaceTB/SmolLM3-3B (3B params) - HuggingFace
3. **Best:** llama-3.1-8b-instant (8B params) - Groq

---

## Performance Metrics

| Rank | Model | Provider | Size | Response Time | Tokens (P/C/T) | Cost |
|------|-------|----------|------|---------------|----------------|------|
"""

        for result in results:
            if "error" in result:
                rank = result['rank']
                model = result['model']
                provider = result['provider']
                size = result['size']
                report += f"| {rank} | {model} | {provider} | {size} | ERROR | - | - |\n"
            else:
                tokens_str = (f"{result.get('prompt_tokens', 0)}/"
                              f"{result.get('completion_tokens', 0)}/"
                              f"{result.get('total_tokens', 0)}")
                cost = "FREE"
                rank = result['rank']
                model = result['model']
                provider = result['provider']
                size = result['size']
                time_s = result['time_seconds']
                report += f"| {rank} | {model} | {provider} | {size} | {time_s}s | {tokens_str} | {cost} |\n"

        report += "\n---\n\n## Response Quality Comparison\n\n"

        for i, result in enumerate(results, 1):
            if "error" in result:
                report += f"### {i}. {result['model']} ({result['rank']})\n\n"
                report += "**Status:** ❌ Error\n\n"
                report += f"**Error Message:** {result['error']}\n\n"
            else:
                report += f"### {i}. {result['model']} ({result['rank']})\n\n"
                report += f"**Response:**\n\n{result['text']}\n\n"
                report += "**Metrics:**\n"
                report += f"- Time: {result['time_seconds']}s\n"
                report += f"- Total tokens: {result.get('total_tokens', 0)}\n\n"

        report += "---\n\n## Conclusions\n\n"

        # Add analysis
        if len(results) == 3 and all("error" not in r for r in results):
            fastest = min(results, key=lambda x: x['time_seconds'])
            slowest = max(results, key=lambda x: x['time_seconds'])

            report += "### Speed Analysis\n\n"
            report += f"- **Fastest:** {fastest['model']} ({fastest['time_seconds']}s)\n"
            report += f"- **Slowest:** {slowest['model']} ({slowest['time_seconds']}s)\n\n"

            report += "### Size vs Performance\n\n"
            report += "- Smaller models (1.5B-3B) are typically faster but may produce lower quality responses\n"
            report += "- Larger models (8B+) take more time but generally provide better quality and coherence\n\n"

        report += "### Cost Analysis\n\n"
        report += "- **HuggingFace Inference API:** Free tier with rate limits\n"
        report += "- **Groq API:** Free tier with generous limits\n"
        report += "- **Total Cost:** $0.00 (all free tier usage)\n\n"

        report += "## Model Links\n\n"
        report += "1. [katanemo/Arch-Router-1.5B](https://huggingface.co/katanemo/Arch-Router-1.5B)\n"
        report += "2. [HuggingFaceTB/SmolLM3-3B](https://huggingface.co/HuggingFaceTB/SmolLM3-3B)\n"
        report += ("3. [meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)"
                   " (via Groq API)\n\n")

        return report

    def close(self):
        """Close all API clients."""
        self.hf_client.close()
        self.groq_client.close()


def main():
    """Main function to run the comparison."""
    # Test prompt
    prompt = "Write a short story about autumn."

    # Initialize comparison
    comparison = ModelComparison()

    try:
        # Run comparison
        results = comparison.run_comparison(prompt)

        # Generate report
        report = comparison.generate_report(prompt, results)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_comparison_{timestamp}.md"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✓ Report saved to: {filename}")

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for result in results:
            if "error" not in result:
                print(f"\n{result['rank']}: {result['model']}")
                print(f"  Time: {result['time_seconds']}s")
                print(f"  Tokens: {result.get('total_tokens', 0)}")
                print(f"  Preview: {result['text'][:100]}...")

    finally:
        comparison.close()


if __name__ == "__main__":
    main()
