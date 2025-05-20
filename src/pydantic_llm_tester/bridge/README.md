1) First read
docs/BRIEF_FOR_LLM.md
2) Implement task list from below, stop after each main task for review, but only after tests pass

### Purpose of this module
Bridge makes it easier to integrate pydantic_llm_tester to your project. You call bridge with a pydantic
model, pydantic_llm_tester will call the LLM, and bridge will return the result in a pydantic model. 
