{
    'name': 'AI Chatbot Widget',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Floating AI chatbot widget integrated across the Odoo web client',
    'description': """
AI Chatbot Widget
=================
Adds a floating chat button pinned to the bottom-left corner, visible across
every Odoo backend screen. Clicking it opens a popup chat window where users
can type a query and converse with an LLM.

Features
--------
- Floating toggle button (bottom-left corner), always accessible.
- Popup chat window with message history, typing indicator, and Enter-to-send.
- Backend controller that forwards messages to an OpenAI-compatible chat
  completions API.
- API key / URL / model configurable from Settings > General Settings
  (no code changes needed to switch providers).
""",
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ai_chatbot_new/static/src/scss/chatbot_widget.scss',
            'ai_chatbot_new/static/src/js/chatbot_widget.js',
            'ai_chatbot_new/static/src/xml/chatbot_widget.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
