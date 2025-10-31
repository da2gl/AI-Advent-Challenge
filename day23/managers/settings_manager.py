"""Settings manager for system instructions and generation config."""

from rich.console import Console


class SettingsManager:
    """Manages system instructions and generation settings."""

    DEFAULT_SYSTEM_INSTRUCTION = "You are a helpful AI assistant."

    def __init__(self, console: Console):
        """
        Initialize settings manager.

        Args:
            console: Rich console for output
        """
        self.console = console
        self.system_instruction = self.DEFAULT_SYSTEM_INSTRUCTION
        self.temperature = 0.7
        self.top_k = 40
        self.top_p = 0.95
        self.max_output_tokens = 2048

    def manage_system_instruction(self):
        """Display and optionally change system instruction."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("System Instruction Management", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print(f"Current: {self.system_instruction}", style="dim")
        self.console.print("=" * 50, style="bright_cyan")

        choice = input("\nEnter new instruction (or press Enter to keep current): ").strip()
        if choice:
            self.system_instruction = choice
            self.console.print("✓ System instruction updated", style="green")

    def manage_generation_settings(self):
        """Display and optionally change generation settings."""
        self.console.print("\n" + "=" * 50, style="bright_cyan")
        self.console.print("Generation Settings", style="yellow")
        self.console.print("=" * 50, style="bright_cyan")
        self.console.print(f"1. Temperature:       {self.temperature} (0.0-2.0)", style="dim")
        self.console.print(f"2. Top K:             {self.top_k} (1-100)", style="dim")
        self.console.print(f"3. Top P:             {self.top_p} (0.0-1.0)", style="dim")
        self.console.print(f"4. Max Output Tokens: {self.max_output_tokens}", style="dim")
        self.console.print("=" * 50, style="bright_cyan")

        choice = input("\nSelect setting to change (1-4) or press Enter to skip: ").strip()

        if choice == "1":
            new_val = input(f"Enter new temperature (current: {self.temperature}): ").strip()
            try:
                val = float(new_val)
                if 0.0 <= val <= 2.0:
                    self.temperature = val
                    self.console.print(f"✓ Temperature set to {val}", style="green")
                else:
                    self.console.print("✗ Temperature must be between 0.0 and 2.0", style="red")
            except ValueError:
                self.console.print("✗ Invalid number", style="red")
        elif choice == "2":
            new_val = input(f"Enter new top K (current: {self.top_k}): ").strip()
            try:
                val = int(new_val)
                if val >= 1:
                    self.top_k = val
                    self.console.print(f"✓ Top K set to {val}", style="green")
                else:
                    self.console.print("✗ Top K must be at least 1", style="red")
            except ValueError:
                self.console.print("✗ Invalid number", style="red")
        elif choice == "3":
            new_val = input(f"Enter new top P (current: {self.top_p}): ").strip()
            try:
                val = float(new_val)
                if 0.0 <= val <= 1.0:
                    self.top_p = val
                    self.console.print(f"✓ Top P set to {val}", style="green")
                else:
                    self.console.print("✗ Top P must be between 0.0 and 1.0", style="red")
            except ValueError:
                self.console.print("✗ Invalid number", style="red")
        elif choice == "4":
            new_val = input(f"Enter new max output tokens (current: {self.max_output_tokens}): ").strip()
            try:
                val = int(new_val)
                if val >= 1:
                    self.max_output_tokens = val
                    self.console.print(f"✓ Max output tokens set to {val}", style="green")
                else:
                    self.console.print("✗ Max tokens must be at least 1", style="red")
            except ValueError:
                self.console.print("✗ Invalid number", style="red")
