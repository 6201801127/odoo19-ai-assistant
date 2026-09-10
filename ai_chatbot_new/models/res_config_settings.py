# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_chatbot_new_api_key = fields.Char(
        string='AI Chatbot API Key',
        config_parameter='ai_chatbot_new.api_key',
        help='API key for the LLM provider (e.g. OpenAI, Azure OpenAI, or any '
             'OpenAI-compatible endpoint).',
    )
    ai_chatbot_new_api_url = fields.Char(
        string='AI Chatbot API URL',
        config_parameter='ai_chatbot_new.api_url',
        default='https://api.openai.com/v1/chat/completions',
        help='Chat completions endpoint URL.',
    )
    ai_chatbot_new_model = fields.Char(
        string='AI Chatbot Model',
        config_parameter='ai_chatbot_new.model',
        default='gpt-4o-mini',
        help='Model name to request from the configured endpoint.',
    )

    ai_chatbot_provider = fields.Selection(
        selection=[
            ('openai', 'OpenAI-compatible (OpenAI, Azure, Groq, Ollama, etc.)'),
            ('gemini', 'Google Gemini'),
            ('anthropic', 'Anthropic Claude'),
        ],
        string='AI Provider',
        config_parameter='ai_chatbot_new.provider',
        default='openai',
    )
