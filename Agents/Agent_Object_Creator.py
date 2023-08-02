protagonist = DialogueAgent(
    name=protagonist_name,
    system_message=protagonist_system_message,
    model=ChatOpenAI(temperature=0.2),
)
storyteller = DialogueAgent(
    name=storyteller_name,
    system_message=storyteller_system_message,
    model=ChatOpenAI(temperature=0.2),
)