# -*- coding: utf-8 -*-
import json
import logging

import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30  # seconds
MAX_HISTORY_MESSAGES = 10  # cap conversation context sent to the LLM

SYSTEM_PROMPT = (
    'You are a helpful assistant embedded inside an Odoo ERP system. '
    'Answer clearly and concisely.'
)


class AiChatbotController(http.Controller):

    @http.route('/ai_chatbot_new/send_message', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def send_message(self, message, history=None, **kwargs):
        """Single entry point for any configured LLM provider. Which
        request/response format to use is picked via the 'ai_chatbot_new.provider'
        system parameter (openai / gemini / anthropic), set from
        Settings > AI Chatbot.
        """
        message = (message or '').strip()
        if not message:
            return {'reply': 'Please enter a message.'}

        ICP = request.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('ai_chatbot_new.api_key')
        api_url = ICP.get_param('ai_chatbot_new.api_url')
        model = ICP.get_param('ai_chatbot_new.model') or 'gpt-4o-mini'
        provider = (ICP.get_param('ai_chatbot_new.provider') or 'openai').lower()
        if not api_key:
            return {
                'reply': (
                    'The AI Chatbot is not configured yet. An administrator '
                    'needs to set the API Key under Settings > AI Chatbot.'
                )
            }

        handler = PROVIDER_HANDLERS.get(provider)
        if handler is None:
            _logger.error('AI Chatbot: unknown provider "%s"', provider)
            return {'reply': f'Unknown AI provider "{provider}" configured. Check Settings > AI Chatbot.'}

        try:
            reply = handler(api_url=api_url, api_key=api_key, model=model,
                             message=message, history=history)
            return {'reply': reply}

        except requests.exceptions.Timeout:
            _logger.warning('AI Chatbot: request timed out (provider=%s)', provider)
            return {'reply': 'The AI service took too long to respond. Please try again.'}

        except requests.exceptions.RequestException as exc:
            resp = getattr(exc, 'response', None)
            body_text = resp.text[:500] if resp is not None else ''
            _logger.error('AI Chatbot: request error (provider=%s) - %s | body: %s',
                           provider, exc, body_text)
            return {'reply': 'Sorry, I could not reach the AI service right now.'}

        except (KeyError, IndexError, ValueError, TypeError) as exc:
            _logger.error('AI Chatbot: unexpected response format (provider=%s) - %s',
                           provider, exc)
            return {'reply': 'Sorry, I received an unexpected response from the AI service.'}


# ==========================================================================
# Provider handlers
#
# Every handler has the same signature (api_url, api_key, model, message,
# history) -> reply_text (str), and raises requests exceptions / KeyError /
# IndexError / ValueError on failure - the caller above handles those
# uniformly. To support a new provider: write one handler function with
# this signature and add it to PROVIDER_HANDLERS at the bottom.
# ==========================================================================

def _recent_turns(history):
    """Normalize + cap incoming history to a plain list of (role, content)."""
    turns = []
    if isinstance(history, list):
        for turn in history[-MAX_HISTORY_MESSAGES:]:
            role = turn.get('role')
            content = turn.get('content')
            if role in ('user', 'assistant') and content:
                turns.append((role, content))
    return turns


def _call_openai_compatible(api_url, api_key, model, message, history):
    """Covers OpenAI, Azure OpenAI, Groq, Together AI, Mistral, DeepSeek,
    OpenRouter, Ollama, LM Studio, and any other provider implementing the
    OpenAI /chat/completions schema - the de facto standard most vendors
    mirror. This is the default/fallback handler."""
    url = api_url or 'https://api.openai.com/v1/chat/completions'

    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    for role, content in _recent_turns(history):
        messages.append({'role': role, 'content': content})
    messages.append({'role': 'user', 'content': message})

    payload = {'model': model, 'messages': messages, 'temperature': 0.3}
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data['choices'][0]['message']['content'].strip()


def _call_gemini(api_url, api_key, model, message, history):
    """Google Gemini generateContent endpoint. Different auth scheme
    (x-goog-api-key header, not Bearer) and payload shape (contents/parts,
    not messages) from OpenAI."""
    base = api_url or 'https://generativelanguage.googleapis.com/v1beta'
    url = base if ':generateContent' in base else f'{base.rstrip("/")}/models/{model}:generateContent'

    contents = []
    for role, content in _recent_turns(history):
        # Gemini uses "model" instead of "assistant" for the AI's own turns.
        contents.append({'role': 'model' if role == 'assistant' else 'user',
                          'parts': [{'text': content}]})
    contents.append({'role': 'user', 'parts': [{'text': message}]})

    payload = {
        'contents': contents,
        'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'generationConfig': {'temperature': 0.3},
    }
    headers = {
        'x-goog-api-key': api_key,
        'Content-Type': 'application/json',
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data['candidates'][0]['content']['parts'][0]['text'].strip()


def _call_anthropic(api_url, api_key, model, message, history):
    """Anthropic Claude Messages API. Auth via x-api-key header plus a
    required anthropic-version header; system prompt is a top-level field,
    not part of the messages array."""
    url = api_url or 'https://api.anthropic.com/v1/messages'

    messages = []
    for role, content in _recent_turns(history):
        messages.append({'role': role, 'content': content})
    messages.append({'role': 'user', 'content': message})

    payload = {
        'model': model,
        'system': SYSTEM_PROMPT,
        'messages': messages,
        'max_tokens': 1024,
        'temperature': 0.3,
    }
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json',
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data['content'][0]['text'].strip()


PROVIDER_HANDLERS = {
    'openai': _call_openai_compatible,
    'gemini': _call_gemini,
    'anthropic': _call_anthropic,
}