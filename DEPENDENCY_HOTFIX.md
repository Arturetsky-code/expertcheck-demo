# Dependency hotfix

Pinned versions for Streamlit Community Cloud:

- streamlit==1.61.0
- starlette==1.3.1

Reason: Starlette 1.4.0 changes the GZipResponder constructor and is incompatible with Streamlit 1.61.0 middleware, causing HTTP 500 health checks before app.py is executed.
