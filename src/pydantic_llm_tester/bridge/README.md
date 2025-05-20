1) First read
docs/BRIEF_FOR_LLM.md
2) Implement task list from below, stop after each main task for review, but only after tests pass

### Purpose of this renewal:
Bridge makes it easier to integrate pydantic_llm_tester to your project. 

### implementation steps (update here as progressing):
#### Phase 1
[ ]   Extend config pytests
[ ]   Remove any mentioning of enabled_providers.json --- provider enabled/disabled status is determined in pyllm_config.json. Use config manager to access this data (like is_py_models_enabled())

STOP FOR REVIEW

#### Phase 2
[ ]   Create pytests for the following phase
[ ]   Add pyllm_config.json options
    [ ]     Default provider
    [ ]     Default model
    [ ]     Secondary provider
    [ ]     Secondary model
    [ ]     Preferred llm model for pydantic model
    [ ]     Secondary llm model for pydantic model

STOP FOR REVIEW

#### Phase 3
[ ]   Create pytests for the minimum viable implementation
[ ]   Implement src/pydantic_llm_tester/bridge/pyllm_bridge.py
    [ ]     Minimum viable implementation with test model (run the file directly)

STOP FOR REVIEW

    [ ]     Create tests for other functionalities
    [ ]     Implement the other functionalities
