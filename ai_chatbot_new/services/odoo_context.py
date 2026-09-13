# -*- coding: utf-8 -*-

from .odoo_tools import (
    get_current_employee,
    get_my_attendance,
    get_my_leave_balance,
    get_my_tasks,
)


def build_odoo_context(env, message):

    message_lower = (message or "").lower()

    context = {}

    # Employee questions
    if any(word in message_lower for word in [
        "employee",
        "job title",
        "department",
        "designation",
    ]):
        context["employee"] = get_current_employee(env)

    # Leave / Time Off questions
    if any(word in message_lower for word in [
        "leave",
        "leaves",
        "time off",
        "vacation",
    ]):
        context["time_off"] = get_my_leave_balance(env)

    # Attendance questions
    if any(word in message_lower for word in [
        "attendance",
        "check in",
        "check-in",
        "check out",
        "check-out",
        "worked hours",
    ]):
        context["attendance"] = get_my_attendance(env)

    # Project / task questions
    if any(word in message_lower for word in [
        "project",
        "task",
        "tasks",
        "assigned",
    ]):
        context["projects"] = get_my_tasks(env)

    return context