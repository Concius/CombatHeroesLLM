import os
import backoff
from anthropic import Anthropic

# Try to import OpenAI (handle both old and new SDK)
try:
    from openai import OpenAI
    OPENAI_V1 = True
    openai_client = None
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        openai_client = OpenAI(api_key=api_key)
except ImportError:
    OPENAI_V1 = False
    import openai
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        openai.api_key = api_key

completion_tokens = prompt_tokens = 0

# Anthropic setup
anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
anthropic_client = None
if anthropic_key:
    anthropic_client = Anthropic(api_key=anthropic_key)
else:
    print("Warning: ANTHROPIC_API_KEY is not set")

def gpt(prompt, model="gpt-4", temperature=0.7, max_tokens=1000, n=1, stop=None) -> list:
    """Call OpenAI API - supports both old and new SDK versions"""
    global completion_tokens, prompt_tokens
    
    if OPENAI_V1:
        # New OpenAI SDK (v1.0+)
        if openai_client is None:
            raise ValueError("OPENAI_API_KEY not set. Please set it as an environment variable.")
        
        outputs = []
        for _ in range(n):
            response = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop
            )
            outputs.append(response.choices[0].message.content)
            
            # Track tokens
            completion_tokens += response.usage.completion_tokens
            prompt_tokens += response.usage.prompt_tokens
        
        return outputs
    else:
        # Legacy OpenAI SDK (pre-v1.0)
        messages = [{"role": "user", "content": prompt}]
        return chatgpt_legacy(messages, model=model, temperature=temperature, max_tokens=max_tokens, n=n, stop=stop)

def chatgpt_legacy(messages, model="gpt-4", temperature=0.7, max_tokens=1000, n=1, stop=None) -> list:
    """Legacy OpenAI API (pre-v1.0) - kept for compatibility"""
    global completion_tokens, prompt_tokens
    
    @backoff.on_exception(backoff.expo, Exception)
    def completions_with_backoff(**kwargs):
        return openai.ChatCompletion.create(**kwargs)
    
    outputs = []
    while n > 0:
        cnt = min(n, 20)
        n -= cnt
        res = completions_with_backoff(
            model=model, 
            messages=messages, 
            temperature=temperature, 
            max_tokens=max_tokens, 
            n=cnt, 
            stop=stop
        )
        outputs.extend([choice.message.content for choice in res.choices])
        completion_tokens += res.usage.completion_tokens
        prompt_tokens += res.usage.prompt_tokens
    
    return outputs

def claude(prompt, model="claude-sonnet-4-20250514", temperature=0.7, max_tokens=1000, n=1, stop=None) -> list:
    """Call Claude API - supports Anthropic models"""
    global completion_tokens, prompt_tokens
    
    if anthropic_client is None:
        raise ValueError("ANTHROPIC_API_KEY not set. Please set it as an environment variable.")
    
    outputs = []
    for _ in range(n):
        response = anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract text from response
        text = response.content[0].text if response.content else ""
        outputs.append(text)
        
        # Track tokens
        completion_tokens += response.usage.output_tokens
        prompt_tokens += response.usage.input_tokens
    
    return outputs

def get_model(args):
    """
    Factory function to return a model callable based on args.backend
    Compatible with both OpenAI v1.0+ and legacy SDK
    """
    def model_callable(prompt, n=1, stop=None):
        # Determine which API to use based on model name
        if args.backend.startswith('claude'):
            return claude(
                prompt,
                model=args.backend,
                temperature=args.temperature,
                max_tokens=1000,
                n=n,
                stop=stop
            )
        else:
            # Assume OpenAI for gpt-* models
            return gpt(
                prompt,
                model=args.backend,
                temperature=args.temperature,
                max_tokens=1000,
                n=n,
                stop=stop
            )
    
    return model_callable

def gpt_usage(backend="gpt-4"):
    """Track token usage and calculate cost"""
    global completion_tokens, prompt_tokens
    
    # Pricing as of November 2025 (update if needed)
    if backend == "gpt-4":
        cost = completion_tokens / 1000 * 0.06 + prompt_tokens / 1000 * 0.03
    elif backend == "gpt-3.5-turbo":
        cost = completion_tokens / 1000 * 0.002 + prompt_tokens / 1000 * 0.0015
    elif backend == "gpt-4o":
        cost = completion_tokens / 1000 * 0.00250 + prompt_tokens / 1000 * 0.01
    elif backend.startswith("claude-sonnet-4"):
        # Claude Sonnet 4 pricing
        cost = completion_tokens / 1000 * 0.003 + prompt_tokens / 1000 * 0.015
    elif backend.startswith("claude-sonnet"):
        # Claude Sonnet 3.5 pricing
        cost = completion_tokens / 1000 * 0.003 + prompt_tokens / 1000 * 0.015
    elif backend.startswith("claude-opus"):
        cost = completion_tokens / 1000 * 0.015 + prompt_tokens / 1000 * 0.075
    elif backend.startswith("claude-haiku"):
        cost = completion_tokens / 1000 * 0.00025 + prompt_tokens / 1000 * 0.00125
    else:
        cost = 0  # Unknown model
    
    return {
        "completion_tokens": completion_tokens,
        "prompt_tokens": prompt_tokens,
        "cost": cost
    }