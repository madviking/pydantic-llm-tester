1) First read
docs/BRIEF_FOR_LLM.md
2) Implement task list from below, stop after each main task for review, but only after tests pass

### Purpose of this renewal:
Bridge makes it easier to integrate pydantic_llm_tester to your project. 

### implementation steps (update here as progressing):
[ ]   Remove any mentioning of enabled_providers.json
[ ]   Add pyllm_config.json options
    [ ]     Default provider
    [ ]     Default model
    [ ]     Secondary provider
    [ ]     Secondary model
    [ ]     Preferred llm model for pydantic model
    [ ]     Secondary llm model for pydantic model
[ ]   Implement src/pydantic_llm_tester/bridge/pyllm_bridge.py
    [ ]     Model loading based on config (validate that model exists)
    [ ]     
