# -*- coding: utf-8 -*-

from odoo import fields


def get_current_employee(env):
    """Return the employee linked to the current Odoo user."""

    employee = env.user.employee_id

    if not employee:
        return {
            "found": False,
            "message": "The current user is not linked to an employee."}

    return {
        "found": True,
        "employee_id": employee.id,
        "name": employee.name,
        "job_title": employee.job_title,
        "department": employee.department_id.name,
        "work_email": employee.work_email,
    }


def get_my_leave_balance(env):
    """Return validated leave allocations for the current employee."""

    employee = env.user.employee_id

    if not employee:
        return {
            "found": False,
            "message": "The current user is not linked to an employee."
        }

    allocations = env["hr.leave.allocation"].search([
        ("employee_id", "=", employee.id),
        ("state", "=", "validate"),
    ])

    result = []

    for allocation in allocations:
        result.append({
            "leave_type": allocation.holiday_status_id.name,
            "allocated_days": allocation.number_of_days,
        })

    return {
        "found": True,
        "employee": employee.name,
        "leave_balances": result,
    }


def get_my_attendance(env, date_from=None, date_to=None):
    """Return attendance records for the current employee."""

    employee = env.user.employee_id

    if not employee:
        return {
            "found": False,
            "message": "The current user is not linked to an employee."
        }

    domain = [
        ("employee_id", "=", employee.id),
    ]

    if date_from:
        domain.append(("check_in", ">=", date_from))

    if date_to:
        domain.append(("check_in", "<=", date_to))

    attendances = env["hr.attendance"].search(
        domain,
        order="check_in desc",
        limit=50,
    )

    result = []

    for attendance in attendances:
        result.append({
            "check_in": fields.Datetime.to_string(attendance.check_in),
            "check_out": (
                fields.Datetime.to_string(attendance.check_out)
                if attendance.check_out
                else None
            ),
            "worked_hours": attendance.worked_hours,
        })

    return {
        "found": True,
        "employee": employee.name,
        "attendances": result,
    }


def get_my_tasks(env):
    """Return tasks assigned to the current employee/user."""

    user = env.user

    tasks = env["project.task"].search([
        ("user_ids", "in", user.id),
    ], limit=50)

    result = []

    for task in tasks:
        result.append({
            "task_id": task.id,
            "task": task.name,
            "project": task.project_id.name,
            "stage": task.stage_id.name,
            "deadline": fields.Date.to_string(task.date_deadline)
            if task.date_deadline
            else None,
        })

    return {
        "found": True,
        "tasks": result,
    }