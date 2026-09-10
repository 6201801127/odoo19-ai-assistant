/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class AiChatbotWidget extends Component {
    static template = "ai_chatbot_new.ChatbotWidget";
    static props = {};

    setup() {
        this.state = useState({
            isOpen: false,
            messages: [], // { role: "user" | "bot", text: string }
            inputText: "",
            isLoading: false,
        });
        this.messagesRef = useRef("messagesBody");
        this.inputRef = useRef("chatInput");
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            requestAnimationFrame(() => {
                this.inputRef.el?.focus();
                this.scrollToBottom();
            });
        }
    }

    closeChat() {
        this.state.isOpen = false;
    }

    onInput(ev) {
        this.state.inputText = ev.target.value;
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    /**
     * Build the recent conversation history in the {role, content} shape
     * the backend/LLM expects, capped to the last 10 messages.
     */
    buildHistory() {
        return this.state.messages.slice(-10).map((m) => ({
            role: m.role === "user" ? "user" : "assistant",
            content: m.text,
        }));
    }

    async sendMessage() {
        const text = this.state.inputText.trim();
        if (!text || this.state.isLoading) {
            return;
        }

        const history = this.buildHistory();
        this.state.messages.push({ role: "user", text });
        this.state.inputText = "";
        this.state.isLoading = true;
        this.scrollToBottom();

        try {
            const result = await rpc("/ai_chatbot_new/send_message", {
                message: text,
                history,
            });
            this.state.messages.push({
                role: "bot",
                text: result.reply || "Sorry, I couldn't process that.",
            });
        } catch (error) {
            this.state.messages.push({
                role: "bot",
                text: "Sorry, something went wrong while contacting the AI service.",
            });
        } finally {
            this.state.isLoading = false;
            this.scrollToBottom();
        }
    }

    scrollToBottom() {
        requestAnimationFrame(() => {
            const el = this.messagesRef.el;
            if (el) {
                el.scrollTop = el.scrollHeight;
            }
        });
    }
}

registry.category("main_components").add("AiChatbotWidget", {
    Component: AiChatbotWidget,
});
