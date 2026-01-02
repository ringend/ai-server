def echo_handler(text=None, **kwargs):
    return {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

tool = {
    "name": "echo",
    "description": "Echo text back to the caller",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string"}
        },
        "required": ["text"]
    },
    "handler": echo_handler
}

