PRICES_VERIFIED_ON = "2026-08-27"
PRICES = {
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-haiku-4-5": (1.0, 5.0),
}
class UnknownModelPrice(KeyError): pass
def cost_usd(model, input_tokens, output_tokens):
    if model not in PRICES:
        raise UnknownModelPrice(model)
    ip, op = PRICES[model]
    return input_tokens/1_000_000*ip + output_tokens/1_000_000*op
