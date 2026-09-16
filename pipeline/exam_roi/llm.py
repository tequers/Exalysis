"""Request budgets and provider responses, independent of exam interpretation."""

from dataclasses import dataclass, field
import time


class ModelConfigurationError(ValueError):
    """A model request cannot run with the supplied configuration."""


class RequestLimitError(ValueError):
    """A complete request cannot fit the configured model budget."""


class TruncatedResponse(RuntimeError):
    """The provider stopped before completing its answer."""


def estimate_tokens(text):
    """Conservative UTF-8 byte estimate, rather than an English chars/4 guess.

    This deliberately overestimates typical text. An adapter can inject the
    selected model's tokenizer when available. Framing is reserved separately.
    """
    return len(text.encode("utf-8"))


@dataclass(frozen=True)
class RequestLimits:
    context_tokens: int = 128000
    output_tokens: int = 32000
    overhead_tokens: int = 1024

    def __post_init__(self):
        for name in ("context_tokens", "output_tokens", "overhead_tokens"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.output_tokens + self.overhead_tokens >= self.context_tokens:
            raise ValueError("Context must leave room for input after output and framing")

    @classmethod
    def from_env(cls, env, stage):
        return cls(**{field: int(env.get(f"LLM_{key}_STAGE{stage}", default))
                      for field, key, default in (
                          ("context_tokens", "CONTEXT_TOKENS", 128000),
                          ("output_tokens", "MAX_OUTPUT_TOKENS", 32000),
                          ("overhead_tokens", "OVERHEAD_TOKENS", 1024))})

    def check(self, system, user, max_tokens, count_tokens=estimate_tokens):
        if type(max_tokens) is not int or not 0 < max_tokens <= self.output_tokens:
            raise RequestLimitError(
                f"Requested output {max_tokens} exceeds the configured output limit "
                f"{self.output_tokens}. Set LLM_MAX_OUTPUT_TOKENS_STAGE1/STAGE2 to "
                "the selected model's supported limit.")
        needed = count_tokens(system) + count_tokens(user) + self.overhead_tokens + max_tokens
        if needed > self.context_tokens:
            raise RequestLimitError(
                f"Request needs an estimated {needed} tokens including output and framing; "
                f"context limit is {self.context_tokens}. Use a model with more context and "
                "configure LLM_CONTEXT_TOKENS_STAGE1/STAGE2, or supply smaller complete questions.")


def text_from_anthropic(msg):
    # Thinking can exhaust the budget before a text block exists.
    if getattr(msg, "stop_reason", None) in {"max_tokens", "model_context_window_exceeded"}:
        raise TruncatedResponse("Incomplete model output. Split the work or configure a larger supported output budget.")
    if getattr(msg, "stop_reason", None) != "end_turn":
        raise ValueError(f"Model did not finish its answer: {getattr(msg, 'stop_reason', None)}")
    parts = [b.text for b in msg.content
             if getattr(b, "type", None) == "text" and getattr(b, "text", None)]
    if not parts:
        raise ValueError("No text block in model response")
    return "\n".join(parts)


def text_from_openai(resp):
    choice = resp.choices[0]
    if choice.finish_reason == "length":
        raise TruncatedResponse("Incomplete model output. Split the work or configure a larger supported output budget.")
    if choice.finish_reason != "stop":
        raise ValueError(f"Model did not finish its answer: {choice.finish_reason}")
    if not choice.message.content:
        raise ValueError("Empty model response")
    return choice.message.content


@dataclass
class ModelClient:
    """An explicitly supplied SDK client, model, and model-specific limits."""

    client: object
    sdk: str
    model: str
    limits: RequestLimits
    count_tokens: object = estimate_tokens
    attempts: int = 3
    provider: str = ""
    client_factory: object = field(default=None, repr=False)

    def __post_init__(self):
        if self.sdk not in {"anthropic", "openai"}:
            raise ValueError(f"Unsupported SDK family: {self.sdk}")
        if type(self.attempts) is not int or self.attempts < 1:
            raise ValueError("attempts must be a positive integer")

    def __call__(self, system, user, max_tokens=None, model=None):
        if model is not None and model != self.model:
            raise ValueError("An injected ModelClient cannot switch models with different limits")
        max_tokens = self.limits.output_tokens if max_tokens is None else max_tokens
        self.limits.check(system, user, max_tokens, self.count_tokens)
        if self.client is None:
            if self.client_factory is None:
                raise ModelConfigurationError("Supply a model client before analyzing an exam")
            self.client = self.client_factory()
        for attempt in range(self.attempts):
            try:
                if self.sdk == "anthropic":
                    with self.client.messages.stream(
                        model=self.model, max_tokens=max_tokens, system=system,
                        messages=[{"role": "user", "content": user}],
                    ) as stream:
                        return text_from_anthropic(stream.get_final_message())
                return text_from_openai(self.client.chat.completions.create(
                    model=self.model, max_tokens=max_tokens,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}],
                ))
            except (TruncatedResponse, ValueError):
                raise
            except Exception:
                if attempt + 1 == self.attempts:
                    raise
                time.sleep(2 ** (attempt + 1))


def run_batches(items, make_prompt, consume, *, system, client, limits,
                output_estimate=lambda batch: 0, label="work"):
    """Split on input/output estimates or truncation, with at most 2*n-1 calls.

    consume validates each complete answer before it can join the result.
    Prompts are rebuilt after every batch, so discovered labels carry forward.
    A single indivisible item fails rather than losing any of its context.
    """
    if not items:
        return
    user = make_prompt(items)
    try:
        limits.check(system, user, limits.output_tokens,
                     client.count_tokens if isinstance(client, ModelClient) else estimate_tokens)
        if output_estimate(items) > limits.output_tokens:
            raise RequestLimitError(f"Estimated {label} output exceeds {limits.output_tokens} tokens")
    except RequestLimitError as exc:
        if len(items) == 1:
            item = items[0]
            identity = item.get("q_id", "") if isinstance(item, dict) else getattr(item, "q_id", "")
            raise RequestLimitError(
                f"Cannot fit complete {label} {identity}. "
                f"{exc} Increase the selected model's supported budget; no context was discarded.") from exc
    else:
        try:
            answer = client(system, user, max_tokens=limits.output_tokens)
        except TruncatedResponse as exc:
            if len(items) == 1:
                raise TruncatedResponse(
                    f"Incomplete {label} for one indivisible item. Configure a larger supported "
                    "output budget or review this question manually; no partial answer was accepted.") from exc
        else:
            consume(answer, items)
            return
    middle = len(items) // 2
    for half in (items[:middle], items[middle:]):
        run_batches(half, make_prompt, consume, system=system, client=client,
                    limits=limits, output_estimate=output_estimate, label=label)


def configured_model_client(provider, model, limits, *, providers, env, attempts=3):
    """Capture configuration now; open the SDK only when a request is needed.

    The environment mapping is supplied by startup, never read from the process.
    Credentials and provider routing are captured here so later environment changes
    cannot replace them. Budget checks precede SDK and credential validation.
    """
    if provider not in providers:
        raise ModelConfigurationError(f"Unknown LLM provider: {provider}")
    if not model or not model.strip():
        raise ModelConfigurationError("Supply an exact model ID")
    config = dict(providers[provider])
    key_names = (config["key_env"], *config.get("key_env_aliases", ()))
    key = next((env.get(name) for name in key_names if env.get(name)), None)
    if config["sdk"] == "anthropic":
        base_url = config["base_url"] or env.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    else:
        base_url = config["base_url"] or env.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    # None tells the SDK to consult the process environment at construction time.
    # Empty strings explicitly preserve the absence of an organization/project.
    organization = env.get("OPENAI_ORG_ID", "")
    project = env.get("OPENAI_PROJECT_ID", "")

    def create_sdk_client():
        if not key:
            raise ModelConfigurationError(
                f"{config['key_env']} is not set, and reading exams needs AI calls.\n"
                f"       set {config['key_env']}=...       (Windows)\n"
                f"       export {config['key_env']}=...    (macOS/Linux)\n"
                f"       Provider is '{provider}'. Set LLM_PROVIDER to use another.")
        try:
            if config["sdk"] == "anthropic":
                import anthropic
                return anthropic.Anthropic(api_key=key, base_url=base_url)
            import openai
        except ImportError as exc:
            raise ModelConfigurationError(
                f"Install the {config['sdk']} SDK: pip install {config['sdk']}") from exc
        return openai.OpenAI(api_key=key, base_url=base_url,
                             organization=organization, project=project)

    return ModelClient(None, config["sdk"], model, limits,
                       attempts=attempts, provider=provider, client_factory=create_sdk_client)
