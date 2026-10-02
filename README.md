# SkillBridge-Employee-Management-System
# Project introduction
The **Employee Management System** is a web application that allows for the management of all employee information. It allows the company to view and edit all their employees information. It should have a feature to add additional functionality such as employee skills and training records which could be added in the future. 
# Problem statement: 
# Functional Requirements
FR1: The system must allow authorised users to view a list of employees.
FR2: The system must allow users to search for employees.
FR3: The system must allow users to filter employee information where neccessary.
FR4: The system must allow users to view the details of an employee.
FR5: The system must allow authorised users to add a new employee.
FR6: The system must allow authorised users to edit an existing employee.
FR7: The system must allow authorised users to delete an employee.
FR8: The system must validate employee information before saving it.
FR9: The system must give appropriate feedback when an operation succeeds or fails.
FR10: The system must require users to log in and restrict functionality by role (authentication and authorisation).
FR11: The system must provide a focused REST-style Web API for employee data.
# Non-functional Requirements
**Security**: Passwords are encrypted, pages are restricted by role, and input is validated and protected against common attacks (e.g. CSRF, SQL injection, XSS).
**Performance**: Pages load in under 3 seconds, supported by a caching strategy.
**Availability**: The system is available 99% of the time, and can be hosted and deployed to a live environment.
**Reliability**: The system handles errors gracefully, does not crash during normal use, and logs errors for troubleshooting.
**Usability**: The interface is consistent, responsive across devices and easy to use, with clear feedback. A user should be able to add an employee in under 2 minutes.
# Main Application Features
**Employee management (CRUD)**: list, view details, add, edit and delete employees.
**Search and filtering**: find employees by keyword and filter by relevant fields.
**Validation and feedback**: server-side and client-side validation, plus success and error messages.
**Authentication and authorisation**: login and role-based access to restricted functions.
**MVT architecture**: Models, Views and Templates, with business logic separated into a services layer.
**Middleware**: for cross-cutting concerns such as security, logging and error handling.
**Django ORM with SQL Server**: persistent storage through the mssql-django backend.
**Reusable templates**: template includes or custom template tags, with consistent layouts and styling.
**Client-side functionality and responsive design**: JavaScript interactivity that works on desktop and mobile.
**State management and caching**: sessions and a caching strategy for better performance.
**Two-way server-to-client communication**: real-time updates (e.g. WebSockets) so changes appear without a page refresh.
**REST-style Web API**: a focused API for employee data.
**Security controls**: CSRF protection, secure password handling, input sanitisation and restricted routes.
**Testing, logging and troubleshooting**: unit and functional tests, plus logging for diagnosing problems.
**Production build and deployment**: compiled or optimised assets and hosting on a live environment.
