import json
from pathlib import Path
from typing import Dict, Any, Optional


class UserProfile:
    """
    Manages user profile and personalization settings.
    Loads and saves user configuration from/to JSON file.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize UserProfile with config file path.

        Args:
            config_path: Path to user config JSON file. If None, uses default location.
        """
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "data" / "user_config.json"

        self.config_path = Path(config_path)
        self.profile_data = self._load_or_create_default()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Returns default configuration structure.
        """
        return {
            "user_profile": {
                "name": "User",
                "role": "Developer",
                "communication_style": "casual",
                "preferences": {
                    "response_length": "concise",
                    "code_style": "clean",
                    "explanation_level": "intermediate"
                },
                "interests": [],
                "habits": [],
                "timezone": "UTC",
                "language_preference": "English"
            },
            "generation_settings": {
                "temperature": 0.7,
                "top_k": 40,
                "top_p": 0.95,
                "max_output_tokens": 2048
            },
            "system_instruction": "You are a helpful AI assistant."
        }

    def _load_or_create_default(self) -> Dict[str, Any]:
        """
        Load config from file or create default if doesn't exist.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                print("Using default configuration.")
                return self._get_default_config()
        else:
            # Create default config
            default_config = self._get_default_config()
            # Temporarily set profile_data for save() to work
            self.profile_data = default_config
            self.save()
            return default_config

    def save(self) -> bool:
        """
        Save current configuration to file.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.profile_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving config to {self.config_path}: {e}")
            return False

    def get_user_profile(self) -> Dict[str, Any]:
        """Returns user profile data."""
        return self.profile_data.get("user_profile", {})

    def get_generation_settings(self) -> Dict[str, Any]:
        """Returns generation settings."""
        return self.profile_data.get("generation_settings", {})

    def get_system_instruction(self) -> str:
        """Returns system instruction with user context injected."""
        base_instruction = self.profile_data.get("system_instruction", "You are a helpful AI assistant.")

        # Build personalized context
        profile = self.get_user_profile()
        name = profile.get("name", "User")
        role = profile.get("role", "")
        style = profile.get("communication_style", "casual")
        prefs = profile.get("preferences", {})
        interests = profile.get("interests", [])
        habits = profile.get("habits", [])

        # Inject user context into system instruction
        context_parts = []

        if name and name != "User":
            context_parts.append(f"You are assisting {name}")
            if role:
                context_parts[0] += f", who is a {role}"

        if style:
            context_parts.append(f"Use a {style} communication style")

        if prefs:
            pref_text = []
            if prefs.get("response_length"):
                pref_text.append(f"{prefs['response_length']} responses")
            if prefs.get("explanation_level"):
                pref_text.append(f"{prefs['explanation_level']}-level explanations")
            if pref_text:
                context_parts.append(f"Provide {', '.join(pref_text)}")

        if interests:
            context_parts.append(f"User's interests: {', '.join(interests)}")

        if habits:
            context_parts.append(f"User's habits: {', '.join(habits)}")

        # Combine base instruction with context
        if context_parts:
            personalized = base_instruction + "\n\nPersonalization:\n- " + "\n- ".join(context_parts)
            return personalized

        return base_instruction

    def update_profile_field(self, field: str, value: Any) -> bool:
        """
        Update a field in user profile.

        Args:
            field: Field name (e.g., 'name', 'role', 'communication_style')
            value: New value

        Returns:
            True if updated successfully
        """
        if "user_profile" not in self.profile_data:
            self.profile_data["user_profile"] = {}

        self.profile_data["user_profile"][field] = value
        return self.save()

    def update_preference(self, pref_name: str, value: str) -> bool:
        """
        Update a preference in user profile.

        Args:
            pref_name: Preference name (e.g., 'response_length')
            value: New value

        Returns:
            True if updated successfully
        """
        if "user_profile" not in self.profile_data:
            self.profile_data["user_profile"] = {}
        if "preferences" not in self.profile_data["user_profile"]:
            self.profile_data["user_profile"]["preferences"] = {}

        self.profile_data["user_profile"]["preferences"][pref_name] = value
        return self.save()

    def update_generation_setting(self, setting: str, value: Any) -> bool:
        """
        Update a generation setting.

        Args:
            setting: Setting name (e.g., 'temperature', 'top_k')
            value: New value

        Returns:
            True if updated successfully
        """
        if "generation_settings" not in self.profile_data:
            self.profile_data["generation_settings"] = {}

        self.profile_data["generation_settings"][setting] = value
        return self.save()

    def update_system_instruction(self, instruction: str) -> bool:
        """
        Update base system instruction.

        Args:
            instruction: New system instruction

        Returns:
            True if updated successfully
        """
        self.profile_data["system_instruction"] = instruction
        return self.save()

    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults.

        Returns:
            True if reset successfully
        """
        self.profile_data = self._get_default_config()
        return self.save()

    def add_interest(self, interest: str) -> bool:
        """Add an interest to user profile."""
        profile = self.get_user_profile()
        interests = profile.get("interests", [])
        if interest not in interests:
            interests.append(interest)
            return self.update_profile_field("interests", interests)
        return True

    def remove_interest(self, interest: str) -> bool:
        """Remove an interest from user profile."""
        profile = self.get_user_profile()
        interests = profile.get("interests", [])
        if interest in interests:
            interests.remove(interest)
            return self.update_profile_field("interests", interests)
        return True

    def add_habit(self, habit: str) -> bool:
        """Add a habit to user profile."""
        profile = self.get_user_profile()
        habits = profile.get("habits", [])
        if habit not in habits:
            habits.append(habit)
            return self.update_profile_field("habits", habits)
        return True

    def remove_habit(self, habit: str) -> bool:
        """Remove a habit from user profile."""
        profile = self.get_user_profile()
        habits = profile.get("habits", [])
        if habit in habits:
            habits.remove(habit)
            return self.update_profile_field("habits", habits)
        return True
