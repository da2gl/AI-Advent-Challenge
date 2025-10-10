"""Demo mode with predefined prompts for testing token compression."""

from typing import Dict, List
from rich.spinner import Spinner
from rich.live import Live

from conversation import ConversationHistory
from text_manager import TextManager


class DemoPrompts:
    """Predefined prompts for demo mode."""

    SHORT = "Что такое машинное обучение? Объясни кратко."

    LONG = """Объясни кратко основы машинного обучения:

1. Три основных типа ML (supervised, unsupervised, reinforcement)
2. Как работают нейронные сети (базовые принципы)
3. Примеры практического применения
4. Отличие от традиционного программирования
5. Популярные библиотеки (TensorFlow, PyTorch, scikit-learn)
6. Процесс обучения модели
7. Переобучение vs недообучение
8. Основные метрики качества

Ответ должен быть структурированным, с простыми аналогиями."""

    VERY_LONG = (
        "Мне нужно детальное объяснение машинного обучения с примерами и кодом. "
        "Введение в машинное обучение: Машинное обучение (Machine Learning, ML) - это область "
        "искусственного интеллекта, которая дает компьютерам способность обучаться без явного "
        "программирования. Вместо того чтобы писать правила вручную, мы позволяем алгоритмам "
        "находить закономерности в данных самостоятельно. "
        "История и развитие: Машинное обучение существует уже несколько десятилетий. Первые работы "
        "начались в 1950-х годах, когда Артур Сэмюэл создал программу для игры в шашки, которая "
        "училась на своем опыте. С тех пор область значительно развилась, особенно с появлением "
        "больших данных и мощных вычислительных ресурсов. "
        "Типы машинного обучения: "
        "1. Обучение с учителем (Supervised Learning) - это наиболее распространенный тип обучения, "
        "где у нас есть размеченные данные. Модель обучается на примерах с известными ответами. "
        "Примеры задач: Классификация изображений (кошки vs собаки), Прогнозирование цен на недвижимость, "
        "Распознавание рукописного текста, Фильтрация спама в электронной почте, Медицинская диагностика. "
        "Популярные алгоритмы: Линейная регрессия, Логистическая регрессия, Деревья решений, "
        "Случайный лес (Random Forest), Метод опорных векторов (SVM), Нейронные сети. "
        "2. Обучение без учителя (Unsupervised Learning) - здесь данные не размечены, и модель должна "
        "сама найти структуру в данных. Примеры задач: Кластеризация клиентов, Уменьшение размерности данных, "
        "Обнаружение аномалий, Рекомендательные системы. Популярные алгоритмы: K-means кластеризация, "
        "Иерархическая кластеризация, PCA (Метод главных компонент), Автоэнкодеры. "
        "3. Обучение с подкреплением (Reinforcement Learning) - агент учится принимать решения, получая "
        "награды или штрафы за свои действия. Примеры применения: Игровые AI (AlphaGo, шахматы), "
        "Робототехника, Автономные автомобили, Торговые боты. "
        "Нейронные сети и глубокое обучение: Нейронные сети вдохновлены структурой человеческого мозга. "
        "Они состоят из слоев нейронов, которые обрабатывают информацию последовательно. "
        "Основные компоненты: Входной слой (получает данные), Скрытые слои (обрабатывают данные), "
        "Выходной слой (дает результат), Функции активации (добавляют нелинейность), "
        "Веса и смещения (обучаемые параметры). "
        "Глубокое обучение (Deep Learning) - это нейронные сети с множеством слоев, способные решать "
        "очень сложные задачи. "
        "Процесс обучения модели: "
        "1. Сбор и подготовка данных "
        "2. Разделение на обучающую и тестовую выборки "
        "3. Выбор модели и гиперпараметров "
        "4. Обучение модели на тренировочных данных "
        "5. Валидация и настройка параметров "
        "6. Тестирование на отложенной выборке "
        "7. Развертывание в продакшн. "
        "Проблемы и решения: Переобучение (Overfitting) - модель слишком хорошо запоминает тренировочные данные, "
        "плохо работает на новых данных, решение: регуляризация, dropout, больше данных. "
        "Недообучение (Underfitting) - модель слишком простая, не может уловить закономерности, "
        "решение: более сложная модель, больше признаков. "
        "Инструменты и библиотеки: Python - основной язык для ML: TensorFlow - от Google, PyTorch - от Facebook, "
        "scikit-learn - для классических алгоритмов, Keras - высокоуровневый API, pandas - для работы с данными, "
        "NumPy - для численных вычислений. "
        "Метрики качества: Для классификации: Accuracy (точность), Precision (точность предсказаний), "
        "Recall (полнота), F1-score. Для регрессии: MSE (среднеквадратичная ошибка), "
        "MAE (средняя абсолютная ошибка), R² (коэффициент детерминации). "
        "Практические советы: "
        "1. Начните с простых моделей "
        "2. Всегда визуализируйте данные "
        "3. Используйте кросс-валидацию "
        "4. Следите за переобучением "
        "5. Экспериментируйте с признаками "
        "6. Документируйте эксперименты. "
        "Теперь объясни все это еще подробнее, добавь примеры кода на Python, расскажи про современные "
        "архитектуры нейронных сетей (CNN, RNN, Transformer), объясни как работает backpropagation, "
        "градиентный спуск, и оптимизаторы типа Adam и SGD. Также хочу узнать про transfer learning, "
        "data augmentation, batch normalization, и другие современные техники."
    )

    @classmethod
    def get_prompts(cls) -> List[Dict[str, str]]:
        """Get all demo prompts with metadata.

        Returns:
            List of dictionaries with prompt info
        """
        return [
            {"name": "short", "title": "Short prompt (~50 tokens) → 2048 tokens response", "text": cls.SHORT},
            {"name": "long", "title": "Long prompt (~246 tokens) → 2048 tokens response", "text": cls.LONG},
            {"name": "very_long", "title": "Very long prompt (~1600 tokens) → 2048 tokens response", "text": cls.VERY_LONG},
        ]


class DemoMode:
    """Demo mode for testing token compression with predefined prompts."""

    # Special system instruction for demo mode - ensures short responses
    DEMO_SYSTEM_INSTRUCTION = (
        "Ты — AI ассистент для демонстрации работы с токенами. "
        "ВАЖНО: Давай КРАТКИЕ и СЖАТЫЕ ответы (максимум 500-700 токенов). "
        "Отвечай по существу, без лишних деталей. "
        "Структурируй ответ кратко: основная мысль → 2-3 ключевых пункта → короткий вывод."
    )

    def __init__(self, client, conversation, console):
        """Initialize demo mode.

        Args:
            client: GeminiApiClient instance
            conversation: ConversationHistory instance
            console: Rich Console instance
        """
        self.client = client
        self.conversation = conversation
        self.console = console
        self.original_limits = {}

    def run(self, current_model, system_instruction, temperature, top_k, top_p, max_output_tokens):
        """Run demo mode with predefined prompts.

        Args:
            current_model: Current Gemini model
            system_instruction: System instruction for AI
            temperature: Generation temperature
            top_k: Top K parameter
            top_p: Top P parameter
            max_output_tokens: Max output tokens
        """
        self._display_welcome()
        self._setup_demo_limits()

        try:
            self._run_demo_loop(
                current_model,
                system_instruction,
                temperature,
                top_k,
                top_p,
                max_output_tokens
            )
        finally:
            self._restore_limits()

    def _display_welcome(self):
        """Display demo mode welcome message."""
        self.console.print("\n" + "=" * 60, style="bright_magenta")
        self.console.print("🎬 DEMO MODE - Token Compression Demonstration", style="bold bright_magenta")
        self.console.print("=" * 60, style="bright_magenta")
        self.console.print("\nThis demo shows how compression works with reduced limits:", style="yellow")
        self.console.print("  • Context limit: 2,000 tokens (instead of 30,000)", style="dim")
        self.console.print("  • Warning threshold: 1,500 tokens (75%)", style="dim")
        self.console.print("  • Keep recent: 3 messages (instead of 5)", style="dim")
        self.console.print("  • Responses: Forced to be short (500-700 tokens)", style="dim")
        self.console.print("\nThe chat will quickly fill up and trigger compression warnings.", style="yellow")
        self.console.print("\n" + "=" * 60, style="bright_magenta")
        self.console.print("Available demo prompts:", style="yellow")

        for prompt in DemoPrompts.get_prompts():
            tokens = TextManager.estimate_tokens(prompt["text"])
            self.console.print(f"  • {prompt['name']}: {prompt['title']} (~{tokens} tokens)", style="dim")

        self.console.print("\n" + "=" * 60, style="bright_magenta")
        self.console.print("Commands:", style="yellow")
        self.console.print("  /short      - Send short demo prompt", style="dim")
        self.console.print("  /long       - Send long demo prompt", style="dim")
        self.console.print("  /very_long  - Send very long demo prompt", style="dim")
        self.console.print("  /exit_demo  - Exit demo mode", style="dim")
        self.console.print("=" * 60, style="bright_magenta")
        self.console.print()

    def _setup_demo_limits(self):
        """Store original limits and set demo limits."""
        self.original_limits = {
            "max": ConversationHistory.MAX_CONTEXT_TOKENS,
            "threshold": ConversationHistory.SAFE_THRESHOLD,
            "keep": ConversationHistory.KEEP_RECENT_MESSAGES,
        }

        ConversationHistory.MAX_CONTEXT_TOKENS = 2000
        ConversationHistory.SAFE_THRESHOLD = 1500
        ConversationHistory.KEEP_RECENT_MESSAGES = 3

        self.conversation.clear()

    def _restore_limits(self):
        """Restore original limits."""
        ConversationHistory.MAX_CONTEXT_TOKENS = self.original_limits["max"]
        ConversationHistory.SAFE_THRESHOLD = self.original_limits["threshold"]
        ConversationHistory.KEEP_RECENT_MESSAGES = self.original_limits["keep"]

        self.conversation.clear()

        self.console.print("\n" + "=" * 60, style="bright_magenta")
        self.console.print("✓ Exited demo mode - Normal limits restored", style="green")
        self.console.print("=" * 60, style="bright_magenta")

    def _run_demo_loop(self, current_model, system_instruction, temperature, top_k, top_p, max_output_tokens):
        """Run demo mode main loop.

        Args:
            current_model: Current Gemini model
            system_instruction: System instruction
            temperature: Generation temperature
            top_k: Top K parameter
            top_p: Top P parameter
            max_output_tokens: Max output tokens
        """
        while True:
            try:
                self.console.print("\n", end="")
                self.console.print("You: ", style="bold bright_blue", end="")
                user_input = input().strip()

                if not user_input:
                    continue

                # Check for exit
                if user_input.lower() == "/exit_demo":
                    break

                # Handle demo prompt commands
                prompt_text, adjusted_max_tokens = self._handle_demo_command(user_input)
                if prompt_text is None:
                    if user_input.startswith("/"):
                        self.console.print("[red]Unknown command. Use /short, /long, /very_long, or /exit_demo[/red]")
                    else:
                        # Regular user input
                        prompt_text = user_input
                        adjusted_max_tokens = max_output_tokens

                if prompt_text:
                    self._process_prompt(
                        prompt_text,
                        current_model,
                        system_instruction,
                        temperature,
                        top_k,
                        top_p,
                        adjusted_max_tokens or max_output_tokens
                    )

            except KeyboardInterrupt:
                print("\n\nDemo interrupted")
                break
            except Exception as e:
                print(f"\n✗ Error: {str(e)}")
                print("Please try again or type /exit_demo to exit demo mode")

    def _handle_demo_command(self, command: str) -> tuple:
        """Handle demo prompt commands.

        Args:
            command: User command

        Returns:
            Tuple of (prompt_text, max_output_tokens) or (None, None) if command not recognized
        """
        command_lower = command.lower()

        # Map commands to prompts and recommended max_output_tokens
        # Long prompts get shorter responses to demonstrate compression faster
        prompts_map = {
            "/short": (DemoPrompts.SHORT, 2048),      # Short prompt → normal response
            "/long": (DemoPrompts.LONG, 2048),        # Long prompt → short response
            "/very_long": (DemoPrompts.VERY_LONG, 2048),  # Very long prompt → very short response
        }

        if command_lower in prompts_map:
            prompt_text, max_tokens = prompts_map[command_lower]
            tokens = TextManager.estimate_tokens(prompt_text)
            self.console.print(
                f"[dim]→ Loading {command_lower[1:]} prompt "
                f"({tokens:,} tokens, max_output: {max_tokens:,})[/dim]"
            )
            return prompt_text, max_tokens

        return None, None

    def _process_prompt(
        self,
        prompt_text,
        current_model,
        system_instruction,
        temperature,
        top_k,
        top_p,
        max_output_tokens
    ):
        """Process a prompt and display response.

        Args:
            prompt_text: Prompt to send
            current_model: Gemini model
            system_instruction: System instruction (ignored - demo uses its own)
            temperature: Temperature
            top_k: Top K
            top_p: Top P
            max_output_tokens: Max output tokens

        Note:
            Demo mode always uses DEMO_SYSTEM_INSTRUCTION to ensure short responses.
        """
        from chat import ConsoleChat

        # Check if input text is too long and needs compression
        prompt_to_send = prompt_text
        if ConversationHistory.should_compress_input(prompt_text):
            input_tokens = TextManager.estimate_tokens(prompt_text)
            self.console.print(
                f"\n[yellow]⚠️  Input too long ({input_tokens:,} tokens)! Compressing...[/yellow]"
            )
            try:
                # Show spinner during input compression
                spinner = Spinner("dots", text="Compressing input...", style="yellow")
                with Live(spinner, console=self.console, transient=True):
                    summary_result = TextManager.summarize_text(
                        text=prompt_text,
                        client=self.client,
                        max_tokens=2000,  # Compress to max 2000 tokens
                        language="mixed",
                        timeout=15  # 15 second timeout (faster failure)
                    )
                prompt_to_send = summary_result['summary']
                self.console.print(
                    f"[green]✓ Compressed input: {input_tokens:,} → "
                    f"{summary_result['summary_tokens']:,} tokens[/green]"
                )
            except Exception as e:
                self.console.print(f"[red]✗ Compression failed: {str(e)}[/red]")
                self.console.print("[yellow]Sending original text...[/yellow]")

        # Add user message to history (use compressed version if available)
        self.conversation.add_user_message(prompt_to_send)

        # Send request to Gemini with demo-specific system instruction
        spinner = Spinner("dots", text="Thinking...", style="bright_magenta")
        with Live(spinner, console=self.console, transient=True):
            response = self.client.generate_content(
                prompt=prompt_to_send,
                model=current_model,
                conversation_history=self.conversation.get_history(),
                system_instruction=self.DEMO_SYSTEM_INSTRUCTION,  # Always use demo instruction
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                max_output_tokens=max_output_tokens
            )

        # Show response
        self.console.print("Assistant: ", style="bold bright_magenta", end="")
        assistant_text = self.client.extract_text(response)

        # Use ConsoleChat's _print_response method
        chat = ConsoleChat()
        chat.console = self.console
        chat._print_response(assistant_text)

        # Display token usage
        usage = self.client.extract_usage_metadata(response)
        if usage:
            self.conversation.add_tokens(usage['total_tokens'])

            self.console.print(
                f"\n[dim]Tokens: {usage['prompt_tokens']} prompt + "
                f"{usage['response_tokens']} response = "
                f"{usage['total_tokens']} total[/dim]"
            )

            # Show context with DEMO limits
            progress = TextManager.format_token_usage(
                self.conversation.total_tokens,
                ConversationHistory.MAX_CONTEXT_TOKENS
            )
            self.console.print(f"[dim]Context [DEMO]: {progress}[/dim]")

            # Auto-compress if approaching limit
            if self.conversation.should_compress():
                self.console.print(
                    "\n[yellow]⚠️  Context limit reached! Auto-compressing...[/yellow]"
                )
                try:
                    # Show spinner during compression API call
                    spinner = Spinner("dots", text="Compressing conversation history...", style="yellow")
                    with Live(spinner, console=self.console, transient=True):
                        result = self.conversation.compress_history(self.client)

                    if result['messages_compressed'] > 0:
                        self.console.print(
                            f"[green]✓ Compressed {result['messages_compressed']} messages, "
                            f"saved {result['tokens_saved']:,} tokens[/green]"
                        )
                    else:
                        self.console.print(
                            f"[dim]ℹ {result.get('message', 'No compression needed')}[/dim]"
                        )
                except Exception as e:
                    self.console.print(
                        f"[red]✗ Auto-compression failed: {str(e)}[/red]\n"
                        f"[dim]Try reducing message length or clearing history with /clear[/dim]"
                    )

        # Add assistant message to history
        self.conversation.add_assistant_message(assistant_text)
