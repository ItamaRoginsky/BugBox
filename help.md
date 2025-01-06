# BugBox  Walkthrough

This document provides a step-by-step guide to exploiting the vulnerabilities in the **BugBox** application. Use this guide responsibly and only on authorized systems.

---

## 1. Login Bypass with SQL Injection

### Steps:
1. Open the **Login** page of BugBox at:
```arduino
http://127.0.0.1:5000/login
```
2. Enter the following payload in the **Username** and **Password** fields:
```sql
' OR '1'='1' --
```
3. Now you`re logged in to the system




## 2. Cross-Site Scripting (XSS) in Comment Feature

### Steps:
1. Navigate to the **User Home** page:
```arduino
http://127.0.0.1:5000/user_home
```
2. Use the **Post a Comment** form and try the following XSS payload:
```html
<script>alert('XSS Exploited');</script>
```
3. Submit the comment.
4. The system runs the xss

## 3. File Upload Vulnerability

### Steps:
1. On the **User Home** page, locate the **Upload a File** section.
2. Create a malicious file, such as a reverse shell payload (e.g., a Meterpreter .exe script).
3. Upload the malicious file using the **Upload File** form.
4. Once the view file is clicked, it will execute automatically on the server due to the vulnerable file handling mechanism.

### Outcome:
- The uploaded file executes on the server without user intervention.
- If the file is a reverse shell, it can establish a connection back to an attacker-controlled system, granting remote access to the server.


## 4. Broken Access Authentication

### Steps:
1. Open the Admin Panel directly by navigating to the following URL:

```arduino
http://127.0.0.1:5000/admin
```
2. Observe that no additional authentication or role validation is required to access this route.

### Outcome:
-Any logged-in user can access the admin panel without proper authorization, demonstrating broken access control and insufficient role validation.



