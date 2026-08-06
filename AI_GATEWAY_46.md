# ExpertCheck 4.6 Alpha 1

## OpenRouter & Groq Intelligence Gateway

- OpenRouter and Groq are primary external providers.
- Automatic failover modes are available in both directions.
- External AI receives only redacted structured project context.
- The advisor offers dedicated tasks for ambiguous objects, cross-check conflicts and checklist gaps.
- AI recommendations never modify the trusted object registry or Core results automatically.

### Streamlit Secrets

```toml
OPENROUTER_API_KEY = "..."
OPENROUTER_MODEL = "openrouter/free"
GROQ_API_KEY = "..."
GROQ_MODEL = "llama-3.3-70b-versatile"
```
