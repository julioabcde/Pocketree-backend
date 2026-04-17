# Pocketree API Documentation

**Version:** 1.0.0

A personal finance management API for tracking accounts, transactions, categories, split bills, and recurring transactions.

---

## Table of Contents

1. [Authentication Overview](#1-authentication-overview)
2. [Auth Endpoints](#2-auth-endpoints)
   - [POST /api/v1/auth/register](#post-apiv1authregister)
   - [POST /api/v1/auth/login](#post-apiv1authlogin)
   - [POST /api/v1/auth/refresh](#post-apiv1authrefresh)
   - [POST /api/v1/auth/logout](#post-apiv1authlogout)
   - [GET /api/v1/auth/me](#get-apiv1authme)
3. [Accounts Endpoints](#3-accounts-endpoints)
   - [POST /api/v1/accounts](#post-apiv1accounts)
   - [GET /api/v1/accounts](#get-apiv1accounts)
   - [GET /api/v1/accounts/summary](#get-apiv1accountssummary)
   - [GET /api/v1/accounts/{account_id}](#get-apiv1accountsaccount_id)
   - [PUT /api/v1/accounts/{account_id}](#put-apiv1accountsaccount_id)
   - [DELETE /api/v1/accounts/{account_id}](#delete-apiv1accountsaccount_id)
4. [Transactions Endpoints](#4-transactions-endpoints)
   - [POST /api/v1/transactions](#post-apiv1transactions)
   - [GET /api/v1/transactions](#get-apiv1transactions)
   - [GET /api/v1/transactions/summary](#get-apiv1transactionssummary)
   - [GET /api/v1/transactions/daily-summary](#get-apiv1transactionsdaily-summary)
   - [POST /api/v1/transactions/transfer](#post-apiv1transactionstransfer)
   - [GET /api/v1/transactions/{transaction_id}](#get-apiv1transactionstransaction_id)
   - [PUT /api/v1/transactions/{transaction_id}](#put-apiv1transactionstransaction_id)
   - [DELETE /api/v1/transactions/{transaction_id}](#delete-apiv1transactionstransaction_id)
5. [Categories Endpoints](#5-categories-endpoints)
   - [POST /api/v1/categories](#post-apiv1categories)
   - [GET /api/v1/categories](#get-apiv1categories)
   - [GET /api/v1/categories/{category_id}](#get-apiv1categoriescategory_id)
   - [PUT /api/v1/categories/{category_id}](#put-apiv1categoriescategory_id)
   - [DELETE /api/v1/categories/{category_id}](#delete-apiv1categoriescategory_id)
6. [Split Bills Endpoints](#6-split-bills-endpoints)
   - [POST /api/v1/split-bills](#post-apiv1split-bills)
   - [GET /api/v1/split-bills](#get-apiv1split-bills)
   - [GET /api/v1/split-bills/summary](#get-apiv1split-billssummary)
   - [GET /api/v1/split-bills/{bill_id}](#get-apiv1split-billsbill_id)
   - [POST /api/v1/split-bills/{bill_id}/calculate](#post-apiv1split-billsbill_idcalculate)
   - [POST /api/v1/split-bills/{bill_id}/debts/{debt_id}/settle](#post-apiv1split-billsbill_iddebtsdebt_idsettle)
   - [DELETE /api/v1/split-bills/{bill_id}](#delete-apiv1split-billsbill_id)
   - [POST /api/v1/split-bills/scan-receipt](#post-apiv1split-billsscan-receipt)
7. [Recurring Transactions Endpoints](#7-recurring-transactions-endpoints)
   - [POST /api/v1/recurring](#post-apiv1recurring)
   - [GET /api/v1/recurring](#get-apiv1recurring)
   - [GET /api/v1/recurring/summary](#get-apiv1recurringsummary)
   - [GET /api/v1/recurring/{recurring_id}](#get-apiv1recurringrecurring_id)
   - [PUT /api/v1/recurring/{recurring_id}](#put-apiv1recurringrecurring_id)
   - [POST /api/v1/recurring/{recurring_id}/execute](#post-apiv1recurringrecurring_idexecute)
   - [DELETE /api/v1/recurring/{recurring_id}](#delete-apiv1recurringrecurring_id)
8. [Reports Endpoints](#8-reports-endpoints)
   - [GET /api/v1/reports/overview](#get-apiv1reportsoverview)
   - [GET /api/v1/reports/cashflow-trend](#get-apiv1reportscashflow-trend)
   - [GET /api/v1/reports/category-breakdown](#get-apiv1reportscategory-breakdown)
   - [GET /api/v1/reports/account-breakdown](#get-apiv1reportsaccount-breakdown)
   - [GET /api/v1/reports/top-transactions](#get-apiv1reportstop-transactions)
   - [GET /api/v1/reports/period-comparison](#get-apiv1reportsperiod-comparison)
9. [Schema Reference](#9-schema-reference)
10. [Enum Reference](#10-enum-reference)
11. [Error Reference](#11-error-reference)

---

## 1. Authentication Overview

Pocketree uses JWT Bearer tokens for authentication. Every request to a protected endpoint must include a valid access token in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

### Token Details

| Token         | Expiry     | Algorithm |
| ------------- | ---------- | --------- |
| Access token  | 60 minutes | HS256     |
| Refresh token | 1 day      | HS256     |

### Token Payload Structure

**Access token:**

```json
{
  "sub": "42",
  "exp": 1710000000,
  "type": "access"
}
```

**Refresh token:**

```json
{
  "sub": "42",
  "exp": 1710086400,
  "type": "refresh"
}
```

### Token Lifecycle

1. Call `POST /api/v1/auth/register` or `POST /api/v1/auth/login` to receive both tokens.
2. Use the `access_token` in the `Authorization` header for all protected endpoints.
3. When the access token expires (HTTP 401), call `POST /api/v1/auth/refresh` with the `refresh_token` to get a new token pair.
4. Call `POST /api/v1/auth/logout` to end the session client-side.

> **Note:** The API does not maintain a server-side token blocklist. Logout is a client-side operation - discard both tokens on the client after calling logout.

---

## 2. Auth Endpoints

### POST /api/v1/auth/register

Registers a new user and returns a token pair. A default **Cash** account is automatically created for the new user.

- **Auth required:** No

**Request Body**

| Field      | Type           | Required | Constraints                                                                                                  |
| ---------- | -------------- | -------- | ------------------------------------------------------------------------------------------------------------ |
| `name`     | string         | Yes      | Non-empty                                                                                                    |
| `email`    | string (email) | Yes      | Valid email format, must be unique                                                                           |
| `password` | string         | Yes      | Min 8 chars; must contain uppercase, lowercase, digit, and special character (`!@#$%^&*()_-+=[]{}; :,.<>/?`) |

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "Secure@123"
}
```

**Response - 201 Created**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**

| Status                   | Detail                     | Cause                                                       |
| ------------------------ | -------------------------- | ----------------------------------------------------------- |
| 409 Conflict             | `Email already registered` | Email is already in use                                     |
| 422 Unprocessable Entity | Validation error detail    | Invalid email format or password does not meet requirements |

---

### POST /api/v1/auth/login

Authenticates an existing user and returns a token pair.

- **Auth required:** No

**Request Body**

| Field      | Type           | Required |
| ---------- | -------------- | -------- |
| `email`    | string (email) | Yes      |
| `password` | string         | Yes      |

```json
{
  "email": "jane@example.com",
  "password": "Secure@123"
}
```

**Response - 200 OK**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**

| Status           | Detail                      | Cause                             |
| ---------------- | --------------------------- | --------------------------------- |
| 401 Unauthorized | `Invalid email or password` | Credentials do not match any user |

---

### POST /api/v1/auth/refresh

Issues a new access token and refresh token using a valid, unexpired refresh token.

- **Auth required:** No (refresh token provided in body)

**Request Body**

| Field           | Type   | Required |
| --------------- | ------ | -------- |
| `refresh_token` | string | Yes      |

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response - 200 OK**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**

| Status           | Detail                             | Cause                                                  |
| ---------------- | ---------------------------------- | ------------------------------------------------------ |
| 401 Unauthorized | `Invalid or expired refresh token` | Token is malformed, expired, or is not a refresh token |
| 401 Unauthorized | `User not found`                   | The user referenced by the token no longer exists      |

---

### POST /api/v1/auth/logout

Ends the current session. The server validates the token but does not blocklist it. Discard both tokens on the client after calling this endpoint.

- **Auth required:** Yes (Bearer access token)

**Request Body:** None

**Response - 200 OK**

```json
{
  "message": "Successfully logged out"
}
```

**Error Responses**

| Status           | Detail                     | Cause                                   |
| ---------------- | -------------------------- | --------------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Token is missing, malformed, or expired |

---

### GET /api/v1/auth/me

Returns the profile of the currently authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body:** None

**Response - 200 OK**

```json
{
  "id": 42,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "created_at": "2026-03-01T10:00:00.000Z",
  "updated_at": "2026-03-01T10:00:00.000Z"
}
```

**Error Responses**

| Status           | Detail                     | Cause                                             |
| ---------------- | -------------------------- | ------------------------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Token is missing, malformed, or expired           |
| 401 Unauthorized | `User not found`           | The user referenced by the token no longer exists |

---

## 3. Accounts Endpoints

All accounts endpoints require a valid Bearer access token. Accounts are scoped to the authenticated user - a user can only read and modify their own accounts.

Accounts are **soft-deleted**: deleting an account sets an `is_deleted` flag rather than removing the record. Soft-deleted accounts are excluded from all list and lookup responses. The uniqueness constraint on `(name, type)` applies only to active accounts, so a deleted account's name/type combination can be reused.

---

### POST /api/v1/accounts

Creates a new account for the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field             | Type        | Required | Constraints                                                                                   |
| ----------------- | ----------- | -------- | --------------------------------------------------------------------------------------------- |
| `name`            | string      | Yes      | 1-100 characters. Leading/trailing whitespace and consecutive internal spaces are normalized. |
| `type`            | AccountType | Yes      | One of: `cash`, `bank_account`, `e_wallet`, `credit_card`                                     |
| `initial_balance` | decimal     | No       | Default `0.00`. Must be `>= 0.00`, max 2 decimal places.                                      |

> The combination of `name` (case-insensitive) and `type` must be unique among the user's active accounts.

```json
{
  "name": "BCA Savings",
  "type": "bank_account",
  "initial_balance": "1500000.00"
}
```

**Response - 201 Created**

```json
{
  "id": 7,
  "name": "BCA Savings",
  "type": "bank_account",
  "balance": "1500000.00",
  "initial_balance": "1500000.00",
  "created_at": "2026-03-13T08:00:00.000Z",
  "updated_at": "2026-03-13T08:00:00.000Z"
}
```

**Error Responses**

| Status                   | Detail                                                          | Cause                                                        |
| ------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------ |
| 401 Unauthorized         | `Invalid or expired token`                                      | Missing or invalid Bearer token                              |
| 409 Conflict             | `An active account with the same name and type already exists.` | Duplicate `(name, type)` for this user                       |
| 422 Unprocessable Entity | Validation error detail                                         | Invalid field values (e.g., negative balance, name too long) |

---

### GET /api/v1/accounts

Returns all active accounts belonging to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body:** None

**Response - 200 OK**

```json
[
  {
    "id": 1,
    "name": "Cash",
    "type": "cash",
    "balance": "0.00",
    "initial_balance": "0.00",
    "created_at": "2026-03-01T10:00:00.000Z",
    "updated_at": "2026-03-01T10:00:00.000Z"
  },
  {
    "id": 7,
    "name": "BCA Savings",
    "type": "bank_account",
    "balance": "1500000.00",
    "initial_balance": "1500000.00",
    "created_at": "2026-03-13T08:00:00.000Z",
    "updated_at": "2026-03-13T08:00:00.000Z"
  }
]
```

Returns an empty array `[]` if the user has no active accounts.

**Error Responses**

| Status           | Detail                     | Cause                           |
| ---------------- | -------------------------- | ------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /api/v1/accounts/summary

Returns an aggregated financial summary across all active accounts for the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Account classification:**

- **Assets** (`total_assets`): `cash`, `bank_account`, `e_wallet`
- **Liabilities** (`total_liabilities`): `credit_card`
- **Net worth** = `total_assets` - `total_liabilities`

**Request Body:** None

**Response - 200 OK**

```json
{
  "total_assets": "1500000.00",
  "total_liabilities": "250000.00",
  "net_worth": "1250000.00",
  "accounts_count": 3
}
```

**Error Responses**

| Status           | Detail                     | Cause                           |
| ---------------- | -------------------------- | ------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /api/v1/accounts/{account_id}

Returns a single active account by ID. The account must belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter    | Type    | Description           |
| ------------ | ------- | --------------------- |
| `account_id` | integer | The ID of the account |

**Response - 200 OK**

```json
{
  "id": 7,
  "name": "BCA Savings",
  "type": "bank_account",
  "balance": "1500000.00",
  "initial_balance": "1500000.00",
  "created_at": "2026-03-13T08:00:00.000Z",
  "updated_at": "2026-03-13T08:00:00.000Z"
}
```

**Error Responses**

| Status           | Detail                                  | Cause                                      |
| ---------------- | --------------------------------------- | ------------------------------------------ |
| 401 Unauthorized | `Invalid or expired token`              | Missing or invalid Bearer token            |
| 403 Forbidden    | `Not authorized to access this account` | Account exists but belongs to another user |
| 404 Not Found    | `Account not found`                     | No active account with this ID exists      |

---

### PUT /api/v1/accounts/{account_id}

Updates the name and/or type of an existing account. Fields not included in the request body are left unchanged. The account must belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter    | Type    | Description                     |
| ------------ | ------- | ------------------------------- |
| `account_id` | integer | The ID of the account to update |

**Request Body**

All fields are optional.

| Field  | Type                | Constraints                                               |
| ------ | ------------------- | --------------------------------------------------------- |
| `name` | string or null      | 1-100 characters if provided. Whitespace is normalized.   |
| `type` | AccountType or null | One of: `cash`, `bank_account`, `e_wallet`, `credit_card` |

> The resulting `(name, type)` combination must remain unique among the user's active accounts, excluding the account being updated.

```json
{
  "name": "BCA Main",
  "type": "bank_account"
}
```

**Response - 200 OK**

```json
{
  "id": 7,
  "name": "BCA Main",
  "type": "bank_account",
  "balance": "1500000.00",
  "initial_balance": "1500000.00",
  "created_at": "2026-03-13T08:00:00.000Z",
  "updated_at": "2026-03-13T09:15:00.000Z"
}
```

**Error Responses**

| Status                   | Detail                                                          | Cause                                                        |
| ------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------ |
| 401 Unauthorized         | `Invalid or expired token`                                      | Missing or invalid Bearer token                              |
| 403 Forbidden            | `Not authorized to access this account`                         | Account belongs to another user                              |
| 404 Not Found            | `Account not found`                                             | No active account with this ID exists                        |
| 409 Conflict             | `An active account with the same name and type already exists.` | Updated `(name, type)` conflicts with another active account |
| 422 Unprocessable Entity | Validation error detail                                         | Invalid field values                                         |

---

### DELETE /api/v1/accounts/{account_id}

Soft-deletes an account. The account is marked as deleted and excluded from all future responses. The account must belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter    | Type    | Description                     |
| ------------ | ------- | ------------------------------- |
| `account_id` | integer | The ID of the account to delete |

**Request Body:** None

**Response - 200 OK**

```json
{
  "message": "Account deleted successfully"
}
```

**Error Responses**

| Status           | Detail                                  | Cause                                 |
| ---------------- | --------------------------------------- | ------------------------------------- |
| 401 Unauthorized | `Invalid or expired token`              | Missing or invalid Bearer token       |
| 403 Forbidden    | `Not authorized to access this account` | Account belongs to another user       |
| 404 Not Found    | `Account not found`                     | No active account with this ID exists |

---

## 4. Transactions Endpoints

All transactions endpoints require a valid Bearer access token. Transactions are scoped to the authenticated user.

Transactions are **soft-deleted**: deleting a transaction sets an `is_deleted` flag. Transfer transactions come in pairs - deleting one automatically deletes its paired counterpart.

---

### POST /api/v1/transactions

Creates a new income or expense transaction for the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field         | Type              | Required | Constraints                                              |
| ------------- | ----------------- | -------- | -------------------------------------------------------- |
| `account_id`  | integer           | Yes      | Must belong to the authenticated user                    |
| `category_id` | integer or null   | No       | Must exist and match the transaction `type`              |
| `type`        | TransactionType   | Yes      | `income` or `expense`                                    |
| `amount`      | decimal           | Yes      | `> 0`, max 2 decimal places                              |
| `date`        | date (YYYY-MM-DD) | Yes      |                                                          |
| `note`        | string or null    | No       | Max 500 characters; leading/trailing whitespace stripped |

```json
{
  "account_id": 7,
  "category_id": 3,
  "type": "expense",
  "amount": "50000.00",
  "date": "2026-03-22",
  "note": "Lunch"
}
```

**Response - 201 Created**

```json
{
  "id": 101,
  "account_id": 7,
  "category_id": 3,
  "type": "expense",
  "amount": "50000.00",
  "date": "2026-03-22",
  "note": "Lunch",
  "transfer_id": null,
  "created_at": "2026-03-22T12:00:00.000Z",
  "updated_at": "2026-03-22T12:00:00.000Z"
}
```

**Error Responses**

| Status                   | Detail                                                      | Cause                                              |
| ------------------------ | ----------------------------------------------------------- | -------------------------------------------------- |
| 400 Bad Request          | `Category type '...' does not match transaction type '...'` | Category type conflicts with transaction type      |
| 401 Unauthorized         | `Invalid or expired token`                                  | Missing or invalid Bearer token                    |
| 404 Not Found            | `Account not found`                                         | Account does not exist or belongs to another user  |
| 404 Not Found            | `Category not found`                                        | Category does not exist or belongs to another user |
| 422 Unprocessable Entity | Validation error detail                                     | Invalid field values                               |

---

### GET /api/v1/transactions

Returns a paginated list of the authenticated user's transactions. Supports filtering and pagination via query parameters.

- **Auth required:** Yes (Bearer access token)

**Query Parameters**

| Parameter     | Type              | Default | Description                         |
| ------------- | ----------------- | ------- | ----------------------------------- |
| `account_id`  | integer           | -       | Filter by account                   |
| `category_id` | integer           | -       | Filter by category                  |
| `type`        | TransactionType   | -       | Filter by `income` or `expense`     |
| `start_date`  | date (YYYY-MM-DD) | -       | Transactions on or after this date  |
| `end_date`    | date (YYYY-MM-DD) | -       | Transactions on or before this date |
| `limit`       | integer           | `20`    | Results per page (1-100)            |
| `offset`      | integer           | `0`     | Number of results to skip           |

**Request Body:** None

**Response - 200 OK**

```json
[
  {
    "id": 101,
    "account_id": 7,
    "category_id": 3,
    "type": "expense",
    "amount": "50000.00",
    "date": "2026-03-22",
    "note": "Lunch",
    "transfer_id": null,
    "created_at": "2026-03-22T12:00:00.000Z",
    "updated_at": "2026-03-22T12:00:00.000Z"
  }
]
```

Returns an empty array `[]` if no transactions match.

**Error Responses**

| Status           | Detail                     | Cause                           |
| ---------------- | -------------------------- | ------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /api/v1/transactions/summary

Returns an aggregated income/expense summary for the authenticated user, optionally filtered.

- **Auth required:** Yes (Bearer access token)

**Query Parameters**

| Parameter     | Type              | Default | Description                     |
| ------------- | ----------------- | ------- | ------------------------------- |
| `account_id`  | integer           | -       | Summary for a specific account  |
| `category_id` | integer           | -       | Summary for a specific category |
| `start_date`  | date (YYYY-MM-DD) | -       | Start date (inclusive)          |
| `end_date`    | date (YYYY-MM-DD) | -       | End date (inclusive)            |

**Request Body:** None

**Response - 200 OK**

```json
{
  "total_income": "500000.00",
  "total_expense": "150000.00",
  "net": "350000.00",
  "transaction_count": 12
}
```

**Error Responses**

| Status           | Detail                     | Cause                           |
| ---------------- | -------------------------- | ------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /api/v1/transactions/daily-summary

Returns a per-day breakdown of income, expense, and net for a given date range. Provide either a `month` shorthand or explicit `start_date` + `end_date`.

- **Auth required:** Yes (Bearer access token)

**Query Parameters**

| Parameter    | Type              | Default | Description                                                                       |
| ------------ | ----------------- | ------- | --------------------------------------------------------------------------------- |
| `month`      | string (YYYY-MM)  | -       | Shorthand for a full calendar month. Mutually exclusive with `start_date`/`end_date`. |
| `start_date` | date (YYYY-MM-DD) | -       | Required if `month` is omitted                                                    |
| `end_date`   | date (YYYY-MM-DD) | -       | Required if `month` is omitted                                                    |
| `account_id` | integer           | -       | Filter by account                                                                 |

> Either `month` or both `start_date` and `end_date` must be provided.

**Request Body:** None

**Response - 200 OK**

Days with no transactions are omitted from the array.

```json
[
  {
    "date": "2026-03-01",
    "income": "500000.00",
    "expense": "150000.00",
    "net": "350000.00"
  },
  {
    "date": "2026-03-05",
    "income": "0.00",
    "expense": "75000.00",
    "net": "-75000.00"
  }
]
```

**Error Responses**

| Status           | Detail                                                               | Cause                                             |
| ---------------- | -------------------------------------------------------------------- | ------------------------------------------------- |
| 400 Bad Request  | `Provide either 'month' or both 'start_date' and 'end_date'`         | Neither `month` nor both date params were provided |
| 401 Unauthorized | `Invalid or expired token`                                           | Missing or invalid Bearer token                   |

---

### POST /api/v1/transactions/transfer

Creates a transfer between two of the authenticated user's accounts. This creates a linked pair of transactions (one `expense` on the source, one `income` on the destination).

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field             | Type              | Required | Constraints                                                   |
| ----------------- | ----------------- | -------- | ------------------------------------------------------------- |
| `from_account_id` | integer           | Yes      | Source account; must belong to the authenticated user         |
| `to_account_id`   | integer           | Yes      | Destination account; must be different from `from_account_id` |
| `amount`          | decimal           | Yes      | `> 0`, max 2 decimal places                                   |
| `date`            | date (YYYY-MM-DD) | Yes      |                                                               |
| `note`            | string or null    | No       | Max 500 characters; leading/trailing whitespace stripped      |

```json
{
  "from_account_id": 1,
  "to_account_id": 7,
  "amount": "200000.00",
  "date": "2026-03-22",
  "note": "Top up savings"
}
```

**Response - 201 Created**

```json
{
  "from_transaction": {
    "id": 102,
    "account_id": 1,
    "category_id": null,
    "type": "expense",
    "amount": "200000.00",
    "date": "2026-03-22",
    "note": "Top up savings",
    "transfer_id": 103,
    "created_at": "2026-03-22T13:00:00.000Z",
    "updated_at": "2026-03-22T13:00:00.000Z"
  },
  "to_transaction": {
    "id": 103,
    "account_id": 7,
    "category_id": null,
    "type": "income",
    "amount": "200000.00",
    "date": "2026-03-22",
    "note": "Top up savings",
    "transfer_id": 102,
    "created_at": "2026-03-22T13:00:00.000Z",
    "updated_at": "2026-03-22T13:00:00.000Z"
  },
  "message": "Transfer completed successfully"
}
```

**Error Responses**

| Status                   | Detail                                         | Cause                                                       |
| ------------------------ | ---------------------------------------------- | ----------------------------------------------------------- |
| 400 Bad Request          | `Transfer failed. Please check your accounts.` | Database integrity error during transfer                    |
| 401 Unauthorized         | `Invalid or expired token`                     | Missing or invalid Bearer token                             |
| 404 Not Found            | `Source account not found`                     | `from_account_id` does not exist or belongs to another user |
| 404 Not Found            | `Destination account not found`                | `to_account_id` does not exist or belongs to another user   |
| 422 Unprocessable Entity | `Cannot transfer to the same account`          | `from_account_id` and `to_account_id` are the same          |

---

### GET /api/v1/transactions/{transaction_id}

Returns a single transaction by ID. The transaction must belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter        | Type    | Description               |
| ---------------- | ------- | ------------------------- |
| `transaction_id` | integer | The ID of the transaction |

**Request Body:** None

**Response - 200 OK**

```json
{
  "id": 101,
  "account_id": 7,
  "category_id": 3,
  "type": "expense",
  "amount": "50000.00",
  "date": "2026-03-22",
  "note": "Lunch",
  "transfer_id": null,
  "created_at": "2026-03-22T12:00:00.000Z",
  "updated_at": "2026-03-22T12:00:00.000Z"
}
```

**Error Responses**

| Status           | Detail                                      | Cause                                     |
| ---------------- | ------------------------------------------- | ----------------------------------------- |
| 401 Unauthorized | `Invalid or expired token`                  | Missing or invalid Bearer token           |
| 403 Forbidden    | `You do not own this transaction`           | Transaction belongs to another user       |
| 404 Not Found    | `Transaction not found`                     | No active transaction with this ID exists |

---

### PUT /api/v1/transactions/{transaction_id}

Updates a transaction. Transfer transactions cannot be modified - delete and recreate instead. All fields are optional; omitted fields are left unchanged.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter        | Type    | Description                         |
| ---------------- | ------- | ----------------------------------- |
| `transaction_id` | integer | The ID of the transaction to update |

**Request Body**

All fields are optional.

| Field         | Type                      | Constraints                                              |
| ------------- | ------------------------- | -------------------------------------------------------- |
| `account_id`  | integer or null           | Must exist and belong to the authenticated user          |
| `category_id` | integer or null           | Must exist and match the original transaction type       |
| `amount`      | decimal or null           | `> 0`, max 2 decimal places                              |
| `date`        | date (YYYY-MM-DD) or null |                                                          |
| `note`        | string or null            | Max 500 characters; leading/trailing whitespace stripped |

```json
{
  "account_id": 8,
  "amount": "75000.00",
  "note": "Dinner"
}
```

**Response - 200 OK**

```json
{
  "id": 101,
  "account_id": 7,
  "category_id": 3,
  "type": "expense",
  "amount": "75000.00",
  "date": "2026-03-22",
  "note": "Dinner",
  "transfer_id": null,
  "created_at": "2026-03-22T12:00:00.000Z",
  "updated_at": "2026-03-22T14:30:00.000Z"
}
```

**Error Responses**

| Status                   | Detail                                                                                | Cause                                                  |
| ------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 400 Bad Request          | `Category type '...' does not match transaction type '...'`                           | Category type conflicts with original transaction type |
| 401 Unauthorized         | `Invalid or expired token`                                                            | Missing or invalid Bearer token                        |
| 403 Forbidden            | `You do not own this transaction`                                                     | Transaction belongs to another user                    |
| 403 Forbidden            | `Not authorized to access this account`                                               | New account belongs to another user                    |
| 403 Forbidden            | `Transfer transactions cannot be modified. Delete the transfer and create a new one.` | Transaction is part of a transfer pair                 |
| 404 Not Found            | `Transaction not found`                                                               | No active transaction with this ID exists              |
| 404 Not Found            | `Category not found`                                                                  | Category does not exist or belongs to another user     |
| 404 Not Found            | `Account not found`                                                                   | Specified account does not exist                       |
| 422 Unprocessable Entity | Validation error detail                                                               | Invalid field values                                   |

---

### DELETE /api/v1/transactions/{transaction_id}

Soft-deletes a transaction. If the transaction is part of a transfer pair, the paired transaction is also deleted.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter        | Type    | Description                         |
| ---------------- | ------- | ----------------------------------- |
| `transaction_id` | integer | The ID of the transaction to delete |

**Request Body:** None

**Response - 200 OK**

```json
{
  "message": "Transaction deleted successfully"
}
```

**Error Responses**

| Status           | Detail                                      | Cause                                     |
| ---------------- | ------------------------------------------- | ----------------------------------------- |
| 401 Unauthorized | `Invalid or expired token`                  | Missing or invalid Bearer token           |
| 403 Forbidden    | `You do not own this transaction`           | Transaction belongs to another user       |
| 404 Not Found    | `Transaction not found`                     | No active transaction with this ID exists |

---

## 5. Categories Endpoints

All categories endpoints require a valid Bearer access token. Categories are scoped to the authenticated user, but users also have access to **system categories** (shared defaults seeded on startup such as Food, Salary, etc.).

Categories support a **two-level hierarchy**: a top-level category can have subcategories, but subcategories cannot themselves have children. System categories cannot be modified or deleted by users.

Categories are **soft-deleted**: deleting a category sets an `is_deleted` flag. A parent category with active subcategories cannot be deleted - delete the subcategories first.

---

### POST /api/v1/categories

Creates a new category for the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field       | Type            | Required | Constraints                                                                                                                   |
| ----------- | --------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `name`      | string          | Yes      | 1-100 characters. Leading/trailing whitespace and consecutive internal spaces are normalized.                                 |
| `type`      | CategoryType    | Yes      | `income` or `expense`                                                                                                         |
| `icon`      | string          | No       | Default `""`. Max 50 characters.                                                                                              |
| `color`     | string          | No       | Default `"#808080"`. Must be in `#RRGGBB` format.                                                                             |
| `parent_id` | integer or null | No       | ID of an existing top-level category. The parent must belong to this user or be a system category, and its `type` must match. |

> The combination of `name` (case-insensitive), `type`, and `parent_id` must be unique among the user's active categories (system categories included). A subcategory name also cannot match any existing top-level category name of the same type.

```json
{
  "name": "Groceries",
  "type": "expense",
  "icon": "cart",
  "color": "#FF6B35",
  "parent_id": 1
}
```

**Response - 201 Created**

```json
{
  "id": 15,
  "name": "Groceries",
  "type": "expense",
  "icon": "cart",
  "color": "#FF6B35",
  "parent_id": 1,
  "is_system": false,
  "created_at": "2026-03-22T10:00:00.000Z",
  "updated_at": "2026-03-22T10:00:00.000Z"
}
```

**Error Responses**

| Status                   | Detail                                                              | Cause                                                     |
| ------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------- |
| 400 Bad Request          | `Parent category not found`                                         | `parent_id` does not reference an active category         |
| 400 Bad Request          | `Invalid parent category`                                           | Parent belongs to another user                            |
| 400 Bad Request          | `Cannot assign a subcategory as a parent`                           | Specified parent is itself a subcategory                  |
| 400 Bad Request          | `Child type must match parent type parent is <type>`                | `type` differs from the parent's type                     |
| 401 Unauthorized         | `Invalid or expired token`                                          | Missing or invalid Bearer token                           |
| 409 Conflict             | `A category with this name already exists`                          | Duplicate `(name, type, parent_id)`                       |
| 409 Conflict             | `Subcategory name cannot match an existing top-level category name` | Name conflicts with a top-level category of the same type |
| 422 Unprocessable Entity | Validation error detail                                             | Invalid field values (e.g., invalid color format)         |

---

### GET /api/v1/categories

Returns all active top-level categories visible to the authenticated user (both system categories and the user's own). Use `parent_id` to retrieve subcategories.

- **Auth required:** Yes (Bearer access token)

**Query Parameters**

| Parameter   | Type         | Default | Description                                                                 |
| ----------- | ------------ | ------- | --------------------------------------------------------------------------- |
| `type`      | CategoryType | -       | Filter by `income` or `expense`                                             |
| `parent_id` | integer      | -       | Return subcategories of this parent. Omit to get top-level categories only. |

**Request Body:** None

**Response - 200 OK**

Results are ordered: system categories first, then alphabetically by name.

```json
[
  {
    "id": 1,
    "name": "Food",
    "type": "expense",
    "icon": "food",
    "color": "#FF6B35",
    "parent_id": null,
    "is_system": true,
    "created_at": "2026-03-01T00:00:00.000Z",
    "updated_at": "2026-03-01T00:00:00.000Z"
  },
  {
    "id": 15,
    "name": "Groceries",
    "type": "expense",
    "icon": "cart",
    "color": "#FF6B35",
    "parent_id": null,
    "is_system": false,
    "created_at": "2026-03-22T10:00:00.000Z",
    "updated_at": "2026-03-22T10:00:00.000Z"
  }
]
```

Returns an empty array `[]` if no categories match.

**Error Responses**

| Status           | Detail                     | Cause                           |
| ---------------- | -------------------------- | ------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /api/v1/categories/{category_id}

Returns a single active category by ID. The category must be a system category or belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter     | Type    | Description            |
| ------------- | ------- | ---------------------- |
| `category_id` | integer | The ID of the category |

**Request Body:** None

**Response - 200 OK**

```json
{
  "id": 15,
  "name": "Groceries",
  "type": "expense",
  "icon": "cart",
  "color": "#FF6B35",
  "parent_id": 1,
  "is_system": false,
  "created_at": "2026-03-22T10:00:00.000Z",
  "updated_at": "2026-03-22T10:00:00.000Z"
}
```

**Error Responses**

| Status           | Detail                                   | Cause                                                                    |
| ---------------- | ---------------------------------------- | ------------------------------------------------------------------------ |
| 401 Unauthorized | `Invalid or expired token`               | Missing or invalid Bearer token                                          |
| 403 Forbidden    | `You don't have access to this category` | Category exists but belongs to another user and is not a system category |
| 404 Not Found    | `Category not found`                     | No active category with this ID exists                                   |

---

### PUT /api/v1/categories/{category_id}

Updates a user-owned category. System categories cannot be edited. All fields are optional; omitted fields are left unchanged.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter     | Type    | Description                      |
| ------------- | ------- | -------------------------------- |
| `category_id` | integer | The ID of the category to update |

**Request Body**

All fields are optional.

| Field   | Type           | Constraints                                             |
| ------- | -------------- | ------------------------------------------------------- |
| `name`  | string or null | 1-100 characters if provided. Whitespace is normalized. |
| `icon`  | string or null | Max 50 characters                                       |
| `color` | string or null | Must be in `#RRGGBB` format                             |

> `type` and `parent_id` cannot be changed after creation.

```json
{
  "name": "Weekly Groceries",
  "color": "#FF8C42"
}
```

**Response - 200 OK**

```json
{
  "id": 15,
  "name": "Weekly Groceries",
  "type": "expense",
  "icon": "cart",
  "color": "#FF8C42",
  "parent_id": 1,
  "is_system": false,
  "created_at": "2026-03-22T10:00:00.000Z",
  "updated_at": "2026-03-22T11:30:00.000Z"
}
```

**Error Responses**

| Status                   | Detail                                            | Cause                                             |
| ------------------------ | ------------------------------------------------- | ------------------------------------------------- |
| 401 Unauthorized         | `Invalid or expired token`                        | Missing or invalid Bearer token                   |
| 403 Forbidden            | `System categories cannot be edited`              | Attempted to edit a system category               |
| 403 Forbidden            | `You don't have permission to edit this category` | Category belongs to another user                  |
| 404 Not Found            | `Category not found`                              | No active category with this ID exists            |
| 409 Conflict             | `A category with this name already exists`        | Updated name conflicts with an existing category  |
| 422 Unprocessable Entity | Validation error detail                           | Invalid field values (e.g., invalid color format) |

---

### DELETE /api/v1/categories/{category_id}

Soft-deletes a user-owned category. System categories cannot be deleted. A parent category with active subcategories cannot be deleted - delete the subcategories first.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter     | Type    | Description                      |
| ------------- | ------- | -------------------------------- |
| `category_id` | integer | The ID of the category to delete |

**Request Body:** None

**Response - 200 OK**

```json
{
  "message": "Category deleted successfully"
}
```

**Error Responses**

| Status           | Detail                                                                              | Cause                                          |
| ---------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------- |
| 401 Unauthorized | `Invalid or expired token`                                                          | Missing or invalid Bearer token                |
| 403 Forbidden    | `System categories cannot be edited`                                                | Attempted to delete a system category          |
| 403 Forbidden    | `You don't have permission to edit this category`                                   | Category belongs to another user               |
| 404 Not Found    | `Category not found`                                                                | No active category with this ID exists         |
| 409 Conflict     | `Cannot delete category with <n> active subcategories. Delete subcategories first.` | Parent category still has active subcategories |

---

## 6. Split Bills Endpoints

All split bills endpoints require a valid Bearer access token. Bills are scoped to the authenticated user.

A split bill tracks a shared expense (e.g., a restaurant bill). The typical workflow is:
1. **Create** a bill with items and optional charges (taxes, tips).
2. **Calculate** the split by providing participants and either equal split (`shares=[]`), custom amounts, or item-based shares - this generates debts.
3. **Settle** individual debts as participants pay each other back.

Bills are **soft-deleted**: deleting a bill sets an `is_deleted` flag.

**Transaction linking (optional):** Split bills can be automatically linked to the personal transaction ledger. To enable this, the bill owner must appear as a participant with their `user_id` set, and provide `account_id` in the request.

**Calculate** — creates an `expense` from the owner's account. Amount depends on owner's role:
- Owner is **payer** (creditor) → expense = `paid_amount`
- Owner is **debtor** → expense = `final_amount` (their share only)
- Owner not in participants → no transaction created (pure manager scenario)

If the bill is recalculated, the old transaction is soft-deleted and replaced.

**Settle** — creates a transaction based on the owner's position in the specific debt being settled:
- Owner is **creditor** of this debt → `income` (receiving payment)
- Owner is **debtor** of this debt → `expense` (paying back)
- Owner not involved in this debt → no transaction created

**Delete** — soft-deletes the bill's linked expense transaction and all settlement transactions (reverses all account balances).

---

### POST /api/v1/split-bills

Creates a new split bill with line items and optional additional charges.

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field               | Type                         | Required | Constraints                                      |
| ------------------- | ---------------------------- | -------- | ------------------------------------------------ |
| `title`             | string                       | Yes      | 1-200 characters; whitespace is normalized       |
| `date`              | date (YYYY-MM-DD)            | Yes      |                                                  |
| `note`              | string or null               | No       | Max 500 characters; leading/trailing whitespace stripped |
| `receipt_image_url` | string or null               | No       | Max 500 characters                               |
| `items`             | list[SplitBillItemInput]     | Yes      | At least 1 item required                         |
| `charges`           | list[SplitBillChargeInput]   | No       | Default `[]`. Additional charges (tax, tip, etc.) |

**SplitBillItemInput**

| Field      | Type    | Required | Constraints                        |
| ---------- | ------- | -------- | ---------------------------------- |
| `name`     | string  | Yes      | 1-200 characters                   |
| `price`    | decimal | Yes      | `> 0`, max 2 decimal places        |
| `quantity` | integer | No       | Default `1`, min `1`               |

**SplitBillChargeInput**

| Field    | Type    | Required | Constraints                                    |
| -------- | ------- | -------- | ---------------------------------------------- |
| `type`   | string  | Yes      | 1-50 characters; normalized to lowercase       |
| `name`   | string  | Yes      | 1-100 characters                               |
| `amount` | decimal | Yes      | `> 0`, max 2 decimal places                    |

```json
{
  "title": "Team Dinner",
  "date": "2026-03-22",
  "note": "Friday team outing",
  "items": [
    { "name": "Steak", "price": "150000.00", "quantity": 2 },
    { "name": "Pasta", "price": "85000.00", "quantity": 1 }
  ],
  "charges": [
    { "type": "tax", "name": "PPN 11%", "amount": "42350.00" },
    { "type": "service", "name": "Service charge", "amount": "38500.00" }
  ]
}
```

**Response - 201 Created**

```json
{
  "id": 1,
  "title": "Team Dinner",
  "subtotal": "385000.00",
  "total_amount": "465850.00",
  "date": "2026-03-22",
  "note": "Friday team outing",
  "receipt_image_url": null,
  "transaction_id": null,
  "created_at": "2026-03-22T19:00:00.000Z",
  "updated_at": "2026-03-22T19:00:00.000Z"
}
```

**Error Responses**

| Status                   | Detail                  | Cause                            |
| ------------------------ | ----------------------- | -------------------------------- |
| 400 Bad Request          | Validation error detail | Business rule violation          |
| 401 Unauthorized         | `Invalid or expired token` | Missing or invalid Bearer token |
| 422 Unprocessable Entity | Validation error detail | Invalid field values             |

---

### GET /api/v1/split-bills

Returns all active split bills belonging to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body:** None

**Response - 200 OK**

```json
[
  {
    "id": 1,
    "title": "Team Dinner",
    "subtotal": "385000.00",
    "total_amount": "465850.00",
    "date": "2026-03-22",
    "note": "Friday team outing",
    "receipt_image_url": null,
    "transaction_id": null,
    "created_at": "2026-03-22T19:00:00.000Z",
    "updated_at": "2026-03-22T19:00:00.000Z"
  }
]
```

Returns an empty array `[]` if the user has no active bills.

**Error Responses**

| Status           | Detail                     | Cause                           |
| ---------------- | -------------------------- | ------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /api/v1/split-bills/summary

Returns split-bill cards summary for Shared/Insights view.

- **Auth required:** Yes (Bearer access token)

**Request Body:** None

**Response - 200 OK**

```json
[
  {
    "id": 1,
    "title": "Team Dinner",
    "date": "2026-03-22",
    "total_amount": "465850.00",
    "participant_count": 3,
    "paid_participant_count": 1,
    "total_non_payer_count": 2,
    "has_calculation": true,
    "is_fully_settled": false,
    "settlement_summary": {
      "total_debt_amount": "232925.00",
      "remaining_debt_amount": "116462.50",
      "settled_debt_count": 1,
      "total_debt_count": 2,
      "settlement_count": 1,
      "settled_amount": "116462.50"
    }
  }
]
```

**Notes**

- Progress `X/Y PAID` is mapped from:
  - `X = paid_participant_count`
  - `Y = total_non_payer_count`
- If a bill has not been calculated yet:
  - `has_calculation = false`
  - `is_fully_settled = false`
  - `paid_participant_count = 0`
  - `total_non_payer_count = 0`

**Error Responses**

| Status           | Detail                     | Cause                           |
| ---------------- | -------------------------- | ------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /api/v1/split-bills/{bill_id}

Returns the full detail of a split bill including items, charges, participants, debts, and settlements.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type    | Description           |
| --------- | ------- | --------------------- |
| `bill_id` | integer | The ID of the bill    |

**Request Body:** None

**Response - 200 OK**

```json
{
  "id": 1,
  "title": "Team Dinner",
  "subtotal": "385000.00",
  "total_amount": "465850.00",
  "date": "2026-03-22",
  "note": "Friday team outing",
  "receipt_image_url": null,
  "transaction_id": null,
  "items": [
    { "id": 1, "name": "Steak", "price": "150000.00", "quantity": 2, "subtotal": "300000.00", "created_at": "2026-03-22T19:00:00.000Z" },
    { "id": 2, "name": "Pasta", "price": "85000.00", "quantity": 1, "subtotal": "85000.00", "created_at": "2026-03-22T19:00:00.000Z" }
  ],
  "charges": [
    { "id": 1, "type": "tax", "name": "PPN 11%", "amount": "42350.00", "created_at": "2026-03-22T19:00:00.000Z" }
  ],
  "participants": [
    {
      "id": 1,
      "user_id": null,
      "name": "Alice",
      "is_payer": true,
      "paid_amount": "465850.00",
      "final_amount": "232925.00",
      "items": [],
      "created_at": "2026-03-22T19:05:00.000Z"
    },
    {
      "id": 2,
      "user_id": 3,
      "name": "Bob",
      "is_payer": false,
      "paid_amount": "0.00",
      "final_amount": "116462.50",
      "items": [
        {
          "item_id": 1,
          "item_name": "Steak",
          "portion": 1,
          "allocated_subtotal": "150000.00"
        }
      ],
      "created_at": "2026-03-22T19:05:00.000Z"
    }
  ],
  "debts": [],
  "settlements": [],
  "paid_participant_count": 1,
  "total_non_payer_count": 2,
  "has_calculation": true,
  "is_fully_settled": false,
  "created_at": "2026-03-22T19:00:00.000Z",
  "updated_at": "2026-03-22T19:00:00.000Z"
}
```

**Error Responses**

| Status           | Detail                     | Cause                                        |
| ---------------- | -------------------------- | -------------------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token              |
| 403 Forbidden    | `You do not own this bill` | Bill belongs to another user                 |
| 404 Not Found    | `Bill not found`           | No active bill with this ID for the user     |

---

### POST /api/v1/split-bills/{bill_id}/calculate

Calculates the split for a bill by assigning participants and share rules. This generates participants, debts, and a plain-text summary.

Supported modes:
- `shares=[]` (or omitted): equal split by subtotal
- Custom amount mode: use `custom_amount` per participant
- Item-based mode: use `item_ids` and optional `share_portions`

Calling this endpoint again replaces the previous calculation only if no settlement exists yet.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type    | Description        |
| --------- | ------- | ------------------ |
| `bill_id` | integer | The ID of the bill |

**Request Body**

| Field          | Type                          | Required | Constraints                  |
| -------------- | ----------------------------- | -------- | ---------------------------- |
| `participants` | list[SplitBillParticipantInput] | Yes    | At least 2 participants required |
| `shares`       | list[ParticipantShare]        | No       | Default `[]` (equal split). If provided, use exactly one mode: custom amounts or item-based assignments. |
| `account_id`   | integer or null               | No       | If provided and owner is in participants, creates an `expense` transaction. Amount = `paid_amount` if owner is payer, `final_amount` if owner is debtor. |

**SplitBillParticipantInput**

| Field         | Type            | Required | Constraints                                                             |
| ------------- | --------------- | -------- | ----------------------------------------------------------------------- |
| `name`        | string          | Yes      | 1-100 characters                                                        |
| `is_payer`    | boolean         | No       | Default `false`. Marks who paid the bill upfront.                       |
| `paid_amount` | decimal         | No       | Default `0.00`. Amount this person paid.                                |
| `user_id`     | integer or null | No       | Link participant to an app user. Required for transaction auto-creation. |

**ParticipantShare**

| Field               | Type              | Required | Description                                                                             |
| ------------------- | ----------------- | -------- | --------------------------------------------------------------------------------------- |
| `participant_index` | integer           | Yes      | 0-based index into the `participants` list. Must be within range.                      |
| `item_ids`          | list[integer]     | No       | Item IDs assigned to this participant (item-based mode). Across all entries, every item must be assigned. |
| `custom_amount`     | decimal or null   | No       | Custom mode only. Must be non-null for every participant in custom mode, and total must equal bill subtotal. |
| `share_portions`    | dict[string, int] | No       | Item-based mode only. Key = item ID as string, value = portions. Every portion must be `> 0`. |

**Validation Rules**

- At least one participant must have `is_payer=true`.
- Sum of `participants[].paid_amount` must equal the bill `total_amount`.
- `custom_amount` and `item_ids` modes cannot be mixed in one request.
- In custom mode, each participant must appear exactly once and all `custom_amount` values are required.
- In item-based mode, duplicate assignment for the same `(item_id, participant_index)` is rejected.
- Once a bill has any settlement, recalculation is rejected.

```json
{
  "participants": [
    { "name": "Alice", "is_payer": true, "paid_amount": "465850.00" },
    { "name": "Bob", "is_payer": false, "paid_amount": "0.00" },
    { "name": "Julio", "is_payer": false, "paid_amount": "0.00", "user_id": 3 }
  ],
  "shares": [
    { "participant_index": 0, "item_ids": [1], "share_portions": { "1": 1 } },
    { "participant_index": 1, "item_ids": [2], "share_portions": { "2": 1 } },
    { "participant_index": 2, "item_ids": [1], "share_portions": { "1": 1 } }
  ],
  "account_id": 7
}
```

**Response - 200 OK**

```json
{
  "title": "Team Dinner",
  "total_amount": "465850.00",
  "participants": [
    { "id": 1, "user_id": null, "name": "Alice", "is_payer": true, "paid_amount": "465850.00", "final_amount": "232925.00", "created_at": "2026-03-22T19:05:00.000Z" },
    { "id": 2, "user_id": null, "name": "Bob", "is_payer": false, "paid_amount": "0.00", "final_amount": "116462.50", "created_at": "2026-03-22T19:05:00.000Z" },
    { "id": 3, "user_id": 3, "name": "Julio", "is_payer": false, "paid_amount": "0.00", "final_amount": "116462.50", "created_at": "2026-03-22T19:05:00.000Z" }
  ],
  "debts": [
    { "id": 1, "debtor_participant_id": 2, "creditor_participant_id": 1, "amount": "116462.50", "remaining_amount": "116462.50", "is_settled": false, "created_at": "2026-03-22T19:05:00.000Z" },
    { "id": 2, "debtor_participant_id": 3, "creditor_participant_id": 1, "amount": "116462.50", "remaining_amount": "116462.50", "is_settled": false, "created_at": "2026-03-22T19:05:00.000Z" }
  ],
  "summary": [
    { "debtor_name": "Bob", "creditor_name": "Alice", "amount": "116462.50", "items": [{ "name": "Pasta", "subtotal": "85000.00" }] }
  ],
  "text": "Bob owes Alice Rp116,462.50\nCarol owes Alice Rp116,462.50"
}
```

**Error Responses**

| Status           | Detail                     | Cause                                    |
| ---------------- | -------------------------- | ---------------------------------------- |
| 400 Bad Request  | Validation error detail (for example: `Invalid participant index: 2`, `Cannot mix custom amounts with item-based shares`, `Custom amounts must be provided for every participant`, `Cannot recalculate a bill with existing settlements. Create a new bill instead.`) | Business rule violation                  |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token          |
| 403 Forbidden    | `You do not own this bill` | Bill belongs to another user             |
| 404 Not Found    | `Bill not found`           | No active bill with this ID for the user |

---

### POST /api/v1/split-bills/{bill_id}/debts/{debt_id}/settle

Records a payment against a specific debt within a bill.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type    | Description        |
| --------- | ------- | ------------------ |
| `bill_id` | integer | The ID of the bill |
| `debt_id` | integer | The ID of the debt |

**Request Body**

| Field        | Type            | Required | Constraints                                                  |
| ------------ | --------------- | -------- | ------------------------------------------------------------ |
| `amount`     | decimal         | Yes      | `> 0`, max 2 decimal places; must not exceed remaining debt  |
| `account_id` | integer or null | No       | If provided and owner is involved in this debt, creates a transaction: `income` if owner is creditor, `expense` if owner is debtor. |

```json
{
  "amount": "116462.50",
  "account_id": 7
}
```

**Response - 200 OK**

```json
{
  "id": 1,
  "debt_id": 1,
  "from_participant_id": 2,
  "to_participant_id": 1,
  "amount": "116462.50",
  "transaction_id": 42,
  "created_at": "2026-03-25T10:00:00.000Z"
}
```

**Error Responses**

| Status           | Detail                     | Cause                                          |
| ---------------- | -------------------------- | ---------------------------------------------- |
| 400 Bad Request  | Validation error detail    | Amount exceeds remaining debt or debt is already settled |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token                |
| 403 Forbidden    | `You do not own this bill` | Bill belongs to another user                   |
| 404 Not Found    | `Bill not found`           | No active bill with this ID for the user       |
| 404 Not Found    | `Debt not found`           | No debt with this ID in the specified bill     |

---

### DELETE /api/v1/split-bills/{bill_id}

Soft-deletes a split bill. Any linked transactions are also soft-deleted and their account balances are reversed:
- The bill's expense transaction (if `account_id` was provided at calculate time)
- All settlement income transactions (if `account_id` was provided at settle time)

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type    | Description               |
| --------- | ------- | ------------------------- |
| `bill_id` | integer | The ID of the bill to delete |

**Request Body:** None

**Response - 200 OK**

```json
{
  "message": "Bill deleted successfully"
}
```

**Error Responses**

| Status           | Detail                     | Cause                                    |
| ---------------- | -------------------------- | ---------------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token          |
| 403 Forbidden    | `You do not own this bill` | Bill belongs to another user             |
| 404 Not Found    | `Bill not found`           | No active bill with this ID for the user |

---

### POST /api/v1/split-bills/scan-receipt

Parses a receipt image using Google Gemini and returns structured line items and charges. Intended as a pre-fill helper for `POST /api/v1/split-bills` — the client decides whether to send the returned data as-is or let the user edit it first.

The server sends the image plus a receipt-parsing prompt to Gemini and parses the model's JSON response. Malformed or unrecognizable output is swallowed silently and returns empty arrays rather than failing.

- **Auth required:** Yes (Bearer access token)
- **Content-Type:** `multipart/form-data`

**Request Body (multipart form field)**

| Field   | Type | Required | Constraints                                               |
| ------- | ---- | -------- | --------------------------------------------------------- |
| `image` | file | Yes      | MIME must be `image/jpeg`, `image/png`, or `image/webp`. Max 5 MB. |

**Response - 200 OK**

```json
{
  "items": [
    { "name": "Steak", "qty": 2, "unit_price": "150000.00" },
    { "name": "Pasta", "qty": 1, "unit_price": "85000.00" }
  ],
  "charges": [
    { "type": "tax", "name": "PPN 11%", "amount": "42350.00" },
    { "type": "service", "name": "Service charge", "amount": "38500.00" }
  ]
}
```

**ReceiptScanItem**

| Field        | Type    | Notes                                                              |
| ------------ | ------- | ------------------------------------------------------------------ |
| `name`       | string  | Clean display name. SKU/barcode prefixes removed.                  |
| `qty`        | integer | `>= 1`. Defaults to `1` if the receipt omits quantity.             |
| `unit_price` | decimal | Price per single unit (not line total). Always `> 0`.              |

**ReceiptScanCharge**

| Field    | Type    | Notes                                                                  |
| -------- | ------- | ---------------------------------------------------------------------- |
| `type`   | string  | Exactly one of `"tax"`, `"service"`, `"discount"`.                     |
| `name`   | string  | Human-readable label, e.g. `"PPN 11%"`, `"Service Charge"`, `"Promo"`. |
| `amount` | decimal | Absolute amount from receipt. Always `> 0`, including discounts.       |

If Gemini cannot extract anything usable, the response is `{"items": [], "charges": []}` with status `200 OK`. The client should handle the empty case as "let user enter manually."

**Error Responses**

| Status                        | Detail                                              | Cause                                                     |
| ----------------------------- | --------------------------------------------------- | --------------------------------------------------------- |
| 400 Bad Request               | `Only JPEG, PNG, or WEBP images are supported`      | Uploaded file has a different MIME type                   |
| 400 Bad Request               | `Uploaded file is empty`                            | `image` field received with 0 bytes                       |
| 401 Unauthorized              | `Invalid or expired token`                          | Missing or invalid Bearer token                           |
| 413 Payload Too Large         | `Image exceeds 5 MB limit`                          | File exceeds 5 MB                                         |
| 502 Bad Gateway               | `Failed to scan receipt: ...`                       | Gemini API returned non-200 or is unreachable             |
| 503 Service Unavailable       | `Receipt scanning is not configured on the server`  | `GEMINI_API_KEY` env var is not set                       |

---

## 7. Recurring Transactions Endpoints

All recurring transactions endpoints require a valid Bearer access token. Recurring transactions are templates that automatically generate real transactions on a schedule.

The scheduler runs every **1 hour** and creates transactions for all active templates whose `next_due_date` has passed (when `auto_create` is `true`). You can also trigger a manual execution via the `/execute` endpoint.

A recurring transaction becomes inactive when:
- `is_active` is set to `false` (via DELETE or PUT)
- `end_date` is reached
- `max_occurrences` is reached

---

### POST /api/v1/recurring

Creates a new recurring transaction template.

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field             | Type                | Required | Constraints                                                                   |
| ----------------- | ------------------- | -------- | ----------------------------------------------------------------------------- |
| `account_id`      | integer             | Yes      | Must belong to the authenticated user                                         |
| `category_id`     | integer or null     | No       | Must exist and match the transaction `type`                                   |
| `type`            | TransactionType     | Yes      | `income` or `expense`                                                         |
| `amount`          | decimal             | Yes      | `> 0`, max 2 decimal places                                                   |
| `frequency`       | RecurringFrequency  | Yes      | `daily`, `weekly`, `monthly`, or `yearly`                                     |
| `day_of_week`     | integer or null     | Conditional | 0-6 (0=Monday, 6=Sunday). Required for `weekly`.                           |
| `day_of_month`    | integer or null     | Conditional | 1-31. Required for `monthly` and `yearly`. Capped to last day of month.    |
| `month_of_year`   | integer or null     | Conditional | 1-12. Required for `yearly`.                                               |
| `start_date`      | date (YYYY-MM-DD)   | Yes      | First date the recurring may execute                                          |
| `end_date`        | date (YYYY-MM-DD) or null | No | Must be after `start_date`. Stop executing after this date.                 |
| `timezone`        | string              | No       | Default `"UTC"`. IANA timezone (e.g., `"Asia/Jakarta"`).                      |
| `auto_create`     | boolean             | No       | Default `true`. If `false`, the scheduler skips this template.                |
| `max_occurrences` | integer or null     | No       | Stop after N executions. `null` = unlimited. Whichever limit (occurrences or end_date) triggers first takes effect. |
| `note`            | string or null      | No       | Max 500 characters; leading/trailing whitespace stripped                      |

> Frequency-specific field rules:
> - `daily`: `day_of_week`, `day_of_month`, and `month_of_year` must all be `null`.
> - `weekly`: `day_of_week` required; `day_of_month` and `month_of_year` must be `null`.
> - `monthly`: `day_of_month` required; `day_of_week` and `month_of_year` must be `null`.
> - `yearly`: `day_of_month` and `month_of_year` required; `day_of_week` must be `null`.

```json
{
  "account_id": 7,
  "category_id": 5,
  "type": "expense",
  "amount": "50000.00",
  "frequency": "monthly",
  "day_of_month": 1,
  "start_date": "2026-04-01",
  "timezone": "Asia/Jakarta",
  "note": "Monthly internet bill"
}
```

**Response - 201 Created**

```json
{
  "id": 1,
  "account_id": 7,
  "category_id": 5,
  "type": "expense",
  "amount": "50000.00",
  "frequency": "monthly",
  "day_of_week": null,
  "day_of_month": 1,
  "month_of_year": null,
  "start_date": "2026-04-01",
  "end_date": null,
  "next_due_date": "2026-04-01",
  "last_run_at": null,
  "timezone": "Asia/Jakarta",
  "auto_create": true,
  "max_occurrences": null,
  "occurrence_count": 0,
  "is_active": true,
  "note": "Monthly internet bill",
  "created_at": "2026-03-27T10:00:00.000Z",
  "updated_at": "2026-03-27T10:00:00.000Z"
}
```

**Error Responses**

| Status                   | Detail                                                      | Cause                                              |
| ------------------------ | ----------------------------------------------------------- | -------------------------------------------------- |
| 400 Bad Request          | `Category type '...' does not match transaction type '...'` | Category type conflicts with transaction type      |
| 401 Unauthorized         | `Invalid or expired token`                                  | Missing or invalid Bearer token                    |
| 404 Not Found            | `Account not found`                                         | Account does not exist or belongs to another user  |
| 404 Not Found            | `Category not found`                                        | Category does not exist or belongs to another user |
| 422 Unprocessable Entity | Validation error detail                                     | Invalid field values or frequency rule violation   |

---

### GET /api/v1/recurring

Returns recurring transaction templates belonging to the authenticated user.
By default, this endpoint returns only active templates.

- **Auth required:** Yes (Bearer access token)

**Query Parameters**

| Parameter | Type   | Default   | Description |
| --------- | ------ | --------- | ----------- |
| `status`  | string | `active`  | Filter by status: `active`, `inactive`, or `all` |

Examples:
- `GET /api/v1/recurring` -> active templates only
- `GET /api/v1/recurring?status=inactive` -> inactive templates only
- `GET /api/v1/recurring?status=all` -> all templates (active first)

**Request Body:** None

**Response - 200 OK**

```json
[
  {
    "id": 1,
    "account_id": 7,
    "category_id": 5,
    "type": "expense",
    "amount": "50000.00",
    "frequency": "monthly",
    "day_of_week": null,
    "day_of_month": 1,
    "month_of_year": null,
    "start_date": "2026-04-01",
    "end_date": null,
    "next_due_date": "2026-05-01",
    "last_run_at": "2026-04-01T00:00:00.000Z",
    "timezone": "Asia/Jakarta",
    "auto_create": true,
    "max_occurrences": null,
    "occurrence_count": 1,
    "is_active": true,
    "note": "Monthly internet bill",
    "created_at": "2026-03-27T10:00:00.000Z",
    "updated_at": "2026-04-01T00:00:00.000Z"
  }
]
```

**Error Responses**

| Status                   | Detail                     | Cause                           |
| ------------------------ | -------------------------- | ------------------------------- |
| 401 Unauthorized         | `Invalid or expired token` | Missing or invalid Bearer token |
| 422 Unprocessable Entity | Validation error detail    | Invalid `status` query value    |

---

### GET /api/v1/recurring/summary

Returns aggregated recurring monthly summary in monthly-equivalent values.

- **Auth required:** Yes (Bearer access token)

Only active recurring templates are included (`income` and `expense`).

Monthly conversion rules:
- `daily` = `amount * 30`
- `weekly` = `amount * 4.345`
- `monthly` = `amount`
- `yearly` = `amount / 12`

Net formula:
- `net_monthly_commitment = total_monthly_income - total_monthly_expense`

**Request Body:** None

**Response - 200 OK**

```json
{
  "total_monthly_income": "1200000.00",
  "total_monthly_expense": "667250.00",
  "net_monthly_commitment": "532750.00"
}
```

**Error Responses**

| Status           | Detail                     | Cause                           |
| ---------------- | -------------------------- | ------------------------------- |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /api/v1/recurring/{recurring_id}

Returns a single recurring transaction template by ID.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter      | Type    | Description                          |
| -------------- | ------- | ------------------------------------ |
| `recurring_id` | integer | The ID of the recurring transaction  |

**Response - 200 OK**

Returns a `RecurringResponse` object (same structure as list response).

**Error Responses**

| Status           | Detail                                        | Cause                                         |
| ---------------- | --------------------------------------------- | --------------------------------------------- |
| 401 Unauthorized | `Invalid or expired token`                    | Missing or invalid Bearer token               |
| 403 Forbidden    | `You do not own this recurring transaction`   | Recurring transaction belongs to another user |
| 404 Not Found    | `Recurring transaction not found`             | No recurring transaction with this ID for the user |

---

### PUT /api/v1/recurring/{recurring_id}

Updates a recurring transaction template. Only the listed fields can be changed; `frequency`, `account_id`, `type`, and schedule fields (`day_of_week`, `day_of_month`, `month_of_year`, `start_date`) cannot be changed after creation.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter      | Type    | Description                                 |
| -------------- | ------- | ------------------------------------------- |
| `recurring_id` | integer | The ID of the recurring transaction to update |

**Request Body**

All fields are optional.

| Field             | Type                      | Constraints                                              |
| ----------------- | ------------------------- | -------------------------------------------------------- |
| `category_id`     | integer or null           | Must exist and match the original transaction type       |
| `amount`          | decimal or null           | `> 0`, max 2 decimal places                              |
| `end_date`        | date (YYYY-MM-DD) or null |                                                          |
| `timezone`        | string or null            | IANA timezone (e.g., `"Asia/Jakarta"`)                   |
| `auto_create`     | boolean or null           |                                                          |
| `max_occurrences` | integer or null           | Min `1`                                                  |
| `is_active`       | boolean or null           |                                                          |
| `note`            | string or null            | Max 500 characters; leading/trailing whitespace stripped |

```json
{
  "amount": "55000.00",
  "note": "Updated internet bill"
}
```

**Response - 200 OK**

Returns the updated `RecurringResponse` object.

**Error Responses**

| Status                   | Detail                                                      | Cause                                              |
| ------------------------ | ----------------------------------------------------------- | -------------------------------------------------- |
| 400 Bad Request          | `Category type '...' does not match transaction type '...'` | Category type conflicts with transaction type      |
| 400 Bad Request          | Validation error detail                                     | Business rule violation                            |
| 401 Unauthorized         | `Invalid or expired token`                                  | Missing or invalid Bearer token                    |
| 403 Forbidden            | `You do not own this recurring transaction`                 | Recurring transaction belongs to another user      |
| 404 Not Found            | `Recurring transaction not found`                           | No recurring transaction with this ID for the user |
| 404 Not Found            | `Category not found`                                        | Category does not exist or belongs to another user |
| 422 Unprocessable Entity | Validation error detail                                     | Invalid field values                               |

---

### POST /api/v1/recurring/{recurring_id}/execute

Manually triggers the execution of a recurring transaction template, creating a real transaction immediately. Execution is skipped (409) if the template is inactive, has already run today, or has reached its limit.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter      | Type    | Description                                   |
| -------------- | ------- | --------------------------------------------- |
| `recurring_id` | integer | The ID of the recurring transaction to execute |

**Request Body:** None

**Response - 200 OK**

```json
{
  "message": "Recurring transaction executed successfully",
  "next_due_date": "2026-06-01",
  "occurrence_count": 2
}
```

**Error Responses**

| Status           | Detail                                                                                   | Cause                                                         |
| ---------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| 400 Bad Request  | Execution error detail                                                                   | Unexpected error during execution                             |
| 401 Unauthorized | `Invalid or expired token`                                                               | Missing or invalid Bearer token                               |
| 403 Forbidden    | `You do not own this recurring transaction`                                              | Recurring transaction belongs to another user                 |
| 404 Not Found    | `Recurring transaction not found`                                                        | No recurring transaction with this ID for the user            |
| 409 Conflict     | `Cannot execute: template is inactive, already ran today, or has reached its limit`      | Template is inactive, ran today already, or limit was reached |

---

### DELETE /api/v1/recurring/{recurring_id}

Deactivates a recurring transaction template (sets `is_active = false`). The template is not deleted and will still appear in list responses.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter      | Type    | Description                                     |
| -------------- | ------- | ----------------------------------------------- |
| `recurring_id` | integer | The ID of the recurring transaction to deactivate |

**Request Body:** None

**Response - 200 OK**

```json
{
  "message": "Recurring transaction deactivated"
}
```

**Error Responses**

| Status           | Detail                            | Cause                                              |
| ---------------- | --------------------------------- | -------------------------------------------------- |
| 401 Unauthorized | `Invalid or expired token`        | Missing or invalid Bearer token                    |
| 403 Forbidden    | `You do not own this recurring transaction` | Recurring transaction belongs to another user      |
| 404 Not Found    | `Recurring transaction not found` | No recurring transaction with this ID for the user |

---

## 8. Reports Endpoints

All reports endpoints are protected and require a Bearer access token.

### Common Query Parameters

| Parameter    | Type              | Required | Default | Notes                                         |
| ------------ | ----------------- | -------- | ------- | --------------------------------------------- |
| `start_date` | date (YYYY-MM-DD) | Yes      | -       | Inclusive                                     |
| `end_date`   | date (YYYY-MM-DD) | Yes      | -       | Inclusive                                     |
| `account_id` | integer           | No       | -       | Filter by account (must belong to the user)   |

- `start_date` must be less than or equal to `end_date` — returns **400** otherwise.
- If `account_id` does not exist or does not belong to the authenticated user, returns **404**.
- All dates are treated as UTC. Timezone offsets are not supported.

---

### GET /api/v1/reports/overview

Returns dashboard-level financial KPIs with previous-period comparison.

**Response - 200 OK**

```json
{
  "total_income": "10000000.00",
  "total_expense": "7000000.00",
  "net": "3000000.00",
  "transaction_count": 120,
  "savings_rate": "30.00",
  "previous_period": {
    "income": "8000000.00",
    "expense": "6000000.00",
    "net": "2000000.00"
  },
  "delta": {
    "income": { "amount": "2000000.00", "percent": "25.00" },
    "expense": { "amount": "1000000.00", "percent": "16.67" },
    "net": { "amount": "1000000.00", "percent": "50.00" }
  }
}
```

Notes:
- Transfer transactions are excluded (`transfer_id IS NULL`).
- `savings_rate = net / income * 100`, rounded to 2 decimals.
- `savings_rate` is `null` when `total_income = 0`.

---

### GET /api/v1/reports/cashflow-trend

Returns time-series cashflow data for charts.

**Additional Query Parameters**

| Parameter  | Type    | Required | Default | Notes                          |
| ---------- | ------- | -------- | ------- | ------------------------------ |
| `group_by` | enum    | No       | `day`   | `day`, `week`, or `month`      |

Range limits:
- `group_by=day`: max 90 days
- `group_by=week`: max 365 days
- `group_by=month`: no enforced max

**Response - 200 OK**

```json
[
  {
    "period": "2026-W15",
    "start_date": "2026-04-06",
    "end_date": "2026-04-12",
    "income": "1000000.00",
    "expense": "500000.00",
    "net": "500000.00",
    "cumulative_net": "500000.00"
  }
]
```

Notes:
- Period label format: `YYYY-MM-DD` (day), `YYYY-Www` (week), `YYYY-MM` (month).
- Includes zero-filled buckets for missing periods.
- `cumulative_net` starts from the first bucket in the requested range.

---

### GET /api/v1/reports/category-breakdown

Returns category distribution for pie/donut charts.

**Additional Query Parameters**

| Parameter | Type              | Required | Default   | Notes                           |
| --------- | ----------------- | -------- | --------- | ------------------------------- |
| `type`    | TransactionType   | No       | `expense` | `income` or `expense`           |
| `top_n`   | integer           | No       | `10`      | 1-20                            |

**Response - 200 OK**

```json
{
  "total_amount": "5000000.00",
  "items": [
    {
      "category_id": 1,
      "name": "Food",
      "color": "#FF6384",
      "icon": "food",
      "amount": "2000000.00",
      "percentage": "40.00",
      "transaction_count": 25
    }
  ]
}
```

Notes:
- `category_id = null` is labeled as `Uncategorized`.
- Percentage is computed in SQL and rounded to 2 decimals.

---

### GET /api/v1/reports/account-breakdown

Returns transaction distribution per account.

**Additional Query Parameters**

| Parameter | Type            | Required | Default   | Notes                 |
| --------- | --------------- | -------- | --------- | --------------------- |
| `type`    | TransactionType | No       | `expense` | `income` or `expense` |

**Response - 200 OK**

```json
{
  "total_amount": "5000000.00",
  "items": [
    {
      "account_id": 1,
      "account_name": "BCA",
      "account_type": "bank_account",
      "amount": "3000000.00",
      "percentage": "60.00",
      "transaction_count": 40
    }
  ]
}
```

---

### GET /api/v1/reports/top-transactions

Returns top transactions by amount.

**Additional Query Parameters**

| Parameter | Type            | Required | Default   | Notes                 |
| --------- | --------------- | -------- | --------- | --------------------- |
| `type`    | TransactionType | No       | `expense` | `income` or `expense` |
| `limit`   | integer         | No       | `5`       | 1-20                  |

**Response - 200 OK**

```json
[
  {
    "transaction_id": 123,
    "date": "2026-04-01",
    "amount": "1000000.00",
    "account": "BCA",
    "category": "Food",
    "note": "Dinner"
  }
]
```

Sorting:
- `amount DESC`
- `date DESC`
- `created_at DESC`

---

### GET /api/v1/reports/period-comparison

Returns current vs previous period metrics.

**Response - 200 OK**

```json
{
  "current_period": {
    "income": "10000000.00",
    "expense": "7000000.00",
    "net": "3000000.00",
    "transaction_count": 120
  },
  "previous_period": {
    "income": "8000000.00",
    "expense": "6000000.00",
    "net": "2000000.00",
    "transaction_count": 100
  },
  "delta": {
    "income": { "amount": "2000000.00", "percent": "25.00" },
    "expense": { "amount": "1000000.00", "percent": "16.67" },
    "net": { "amount": "1000000.00", "percent": "50.00" },
    "transaction_count": { "amount": 20, "percent": "20.00" }
  }
}
```

Notes:
- Previous period uses the same duration as the selected current period.
- `delta.percent` is `null` when previous period baseline is `0`.

---

## 9. Schema Reference

### UserRegister

| Field      | Type   | Required | Notes                                                                        |
| ---------- | ------ | -------- | ---------------------------------------------------------------------------- |
| `name`     | string | Yes      | User's display name                                                          |
| `email`    | string | Yes      | Valid email address                                                          |
| `password` | string | Yes      | Min 8 chars; must include uppercase, lowercase, digit, and special character |

### UserLogin

| Field      | Type   | Required |
| ---------- | ------ | -------- |
| `email`    | string | Yes      |
| `password` | string | Yes      |

### TokenRefresh

| Field           | Type   | Required |
| --------------- | ------ | -------- |
| `refresh_token` | string | Yes      |

### AccountCreate

| Field             | Type        | Required | Default | Notes                                   |
| ----------------- | ----------- | -------- | ------- | --------------------------------------- |
| `name`            | string      | Yes      | -       | 1-100 chars; whitespace is normalized   |
| `type`            | AccountType | Yes      | -       | See [Enum Reference](#9-enum-reference) |
| `initial_balance` | decimal     | No       | `0.00`  | Must be `>= 0.00`; max 2 decimal places |

### AccountUpdate

| Field  | Type                | Required | Notes                                             |
| ------ | ------------------- | -------- | ------------------------------------------------- |
| `name` | string or null      | No       | 1-100 chars if provided; whitespace is normalized |
| `type` | AccountType or null | No       | See [Enum Reference](#9-enum-reference)           |

### TokenResponse

| Field           | Type   | Notes                     |
| --------------- | ------ | ------------------------- |
| `access_token`  | string | JWT; valid for 60 minutes |
| `refresh_token` | string | JWT; valid for 1 day      |
| `token_type`    | string | Always `"bearer"`         |

### UserResponse

| Field        | Type                |
| ------------ | ------------------- |
| `id`         | integer             |
| `name`       | string              |
| `email`      | string              |
| `created_at` | datetime (ISO 8601) |
| `updated_at` | datetime (ISO 8601) |

### MessageResponse

| Field     | Type   |
| --------- | ------ |
| `message` | string |

### AccountResponse

| Field             | Type                | Notes                                    |
| ----------------- | ------------------- | ---------------------------------------- |
| `id`              | integer             |                                          |
| `name`            | string              |                                          |
| `type`            | AccountType         |                                          |
| `balance`         | decimal             | Current balance, updated by transactions |
| `initial_balance` | decimal             | Starting balance set at creation         |
| `created_at`      | datetime (ISO 8601) |                                          |
| `updated_at`      | datetime (ISO 8601) |                                          |

### AccountSummary

| Field               | Type    | Notes                                                           |
| ------------------- | ------- | --------------------------------------------------------------- |
| `total_assets`      | decimal | Sum of balances for `cash`, `bank_account`, `e_wallet` accounts |
| `total_liabilities` | decimal | Sum of balances for `credit_card` accounts                      |
| `net_worth`         | decimal | `total_assets` - `total_liabilities`                            |
| `accounts_count`    | integer | Total number of active accounts                                 |

### TransactionCreate

| Field         | Type              | Required | Default | Notes                                   |
| ------------- | ----------------- | -------- | ------- | --------------------------------------- |
| `account_id`  | integer           | Yes      | -       | Must belong to the authenticated user   |
| `category_id` | integer or null   | No       | `null`  | Must exist and match transaction `type` |
| `type`        | TransactionType   | Yes      | -       | See [Enum Reference](#9-enum-reference) |
| `amount`      | decimal           | Yes      | -       | `> 0`, max 2 decimal places             |
| `date`        | date (YYYY-MM-DD) | Yes      | -       |                                         |
| `note`        | string or null    | No       | `null`  | Max 500 chars; whitespace stripped      |

### TransactionUpdate

| Field         | Type                      | Required | Notes                                          |
| ------------- | ------------------------- | -------- | ---------------------------------------------- |
| `account_id`  | integer or null           | No       | Must exist and belong to the authenticated user |
| `category_id` | integer or null           | No       | Must exist and match original transaction type |
| `amount`      | decimal or null           | No       | `> 0`, max 2 decimal places                    |
| `date`        | date (YYYY-MM-DD) or null | No       |                                                |
| `note`        | string or null            | No       | Max 500 chars; whitespace stripped             |

### TransactionTransfer

| Field             | Type              | Required | Notes                                                   |
| ----------------- | ----------------- | -------- | ------------------------------------------------------- |
| `from_account_id` | integer           | Yes      | Source account; must belong to the authenticated user   |
| `to_account_id`   | integer           | Yes      | Destination account; must differ from `from_account_id` |
| `amount`          | decimal           | Yes      | `> 0`, max 2 decimal places                             |
| `date`            | date (YYYY-MM-DD) | Yes      |                                                         |
| `note`            | string or null    | No       | Max 500 chars; whitespace stripped                      |

### TransactionResponse

| Field         | Type                | Notes                                              |
| ------------- | ------------------- | -------------------------------------------------- |
| `id`          | integer             |                                                    |
| `account_id`  | integer             |                                                    |
| `category_id` | integer or null     |                                                    |
| `type`        | TransactionType     | `income` or `expense`                              |
| `amount`      | decimal             |                                                    |
| `date`        | date (YYYY-MM-DD)   |                                                    |
| `note`        | string or null      |                                                    |
| `transfer_id` | integer or null     | ID of the paired transaction if part of a transfer |
| `created_at`  | datetime (ISO 8601) |                                                    |
| `updated_at`  | datetime (ISO 8601) |                                                    |

### TransferResponse

| Field              | Type                | Notes                                       |
| ------------------ | ------------------- | ------------------------------------------- |
| `from_transaction` | TransactionResponse | The outgoing (expense) side of the transfer |
| `to_transaction`   | TransactionResponse | The incoming (income) side of the transfer  |
| `message`          | string              | Always `"Transfer completed successfully"`  |

### TransactionSummary

| Field               | Type    | Notes                                               |
| ------------------- | ------- | --------------------------------------------------- |
| `total_income`      | decimal | Sum of all income transactions matching the filter  |
| `total_expense`     | decimal | Sum of all expense transactions matching the filter |
| `net`               | decimal | `total_income` - `total_expense`                    |
| `transaction_count` | integer | Total number of matching transactions               |

### DailySummary

| Field     | Type              | Notes                              |
| --------- | ----------------- | ---------------------------------- |
| `date`    | date (YYYY-MM-DD) |                                    |
| `income`  | decimal           | Total income for this day          |
| `expense` | decimal           | Total expense for this day         |
| `net`     | decimal           | `income` - `expense`               |

### CategoryCreate

| Field       | Type            | Required | Default     | Notes                                   |
| ----------- | --------------- | -------- | ----------- | --------------------------------------- |
| `name`      | string          | Yes      | -           | 1-100 chars; whitespace is normalized   |
| `type`      | CategoryType    | Yes      | -           | See [Enum Reference](#9-enum-reference) |
| `icon`      | string          | No       | `""`        | Max 50 chars                            |
| `color`     | string          | No       | `"#808080"` | Must be `#RRGGBB` format                |
| `parent_id` | integer or null | No       | `null`      | Must be an active top-level category    |

### CategoryUpdate

| Field   | Type           | Required | Notes                                             |
| ------- | -------------- | -------- | ------------------------------------------------- |
| `name`  | string or null | No       | 1-100 chars if provided; whitespace is normalized |
| `icon`  | string or null | No       | Max 50 chars                                      |
| `color` | string or null | No       | Must be `#RRGGBB` format                          |

### CategoryResponse

| Field        | Type                | Notes                                 |
| ------------ | ------------------- | ------------------------------------- |
| `id`         | integer             |                                       |
| `name`       | string              |                                       |
| `type`       | CategoryType        | `income` or `expense`                 |
| `icon`       | string              |                                       |
| `color`      | string              | Hex color in `#RRGGBB` format         |
| `parent_id`  | integer or null     | `null` for top-level categories       |
| `is_system`  | boolean             | `true` for built-in system categories |
| `created_at` | datetime (ISO 8601) |                                       |
| `updated_at` | datetime (ISO 8601) |                                       |

### SplitBillResponse

| Field               | Type                | Notes                                   |
| ------------------- | ------------------- | --------------------------------------- |
| `id`                | integer             |                                         |
| `title`             | string              |                                         |
| `subtotal`          | decimal             | Sum of all item subtotals               |
| `total_amount`      | decimal             | `subtotal` + all charges                |
| `date`              | date (YYYY-MM-DD)   |                                         |
| `note`              | string or null      |                                         |
| `receipt_image_url` | string or null      |                                         |
| `created_at`        | datetime (ISO 8601) |                                         |
| `updated_at`        | datetime (ISO 8601) |                                         |

### SplitBillDetailResponse

Extends `SplitBillResponse` with the following additional fields:

| Field          | Type                              | Notes                             |
| -------------- | --------------------------------- | --------------------------------- |
| `items`        | list[SplitBillItemResponse]       |                                   |
| `charges`      | list[SplitBillChargeResponse]     |                                   |
| `participants` | list[SplitBillParticipantDetailResponse] | Includes participant-item mapping |
| `debts`        | list[SplitBillDebtResponse]       |                                   |
| `settlements`  | list[SplitBillSettlementResponse] |                                   |
| `paid_participant_count` | integer | X for `X/Y PAID` |
| `total_non_payer_count` | integer | Y for `X/Y PAID` |
| `has_calculation` | boolean | `true` when bill has been calculated |
| `is_fully_settled` | boolean | `true` when all debts are settled |

### SplitBillSummaryResponse

| Field                    | Type                               | Notes                                  |
| ------------------------ | ---------------------------------- | -------------------------------------- |
| `id`                     | integer                            |                                        |
| `title`                  | string                             |                                        |
| `date`                   | date (YYYY-MM-DD)                  |                                        |
| `total_amount`           | decimal                            |                                        |
| `participant_count`      | integer                            | Includes payers                        |
| `paid_participant_count` | integer                            | X for `X/Y PAID`                       |
| `total_non_payer_count`  | integer                            | Y for `X/Y PAID`                       |
| `has_calculation`        | boolean                            | `false` for bills not yet calculated   |
| `is_fully_settled`       | boolean                            | `false` until calculated and all settled |
| `settlement_summary`     | SplitBillSettlementSummaryResponse | Debt/settlement aggregate per bill     |

### SplitBillItemResponse

| Field        | Type                | Notes                         |
| ------------ | ------------------- | ----------------------------- |
| `id`         | integer             |                               |
| `name`       | string              |                               |
| `price`      | decimal             | Price per unit                |
| `quantity`   | integer             |                               |
| `subtotal`   | decimal             | `price x quantity`            |
| `created_at` | datetime (ISO 8601) |                               |

### SplitBillChargeResponse

| Field        | Type                | Notes                              |
| ------------ | ------------------- | ---------------------------------- |
| `id`         | integer             |                                    |
| `type`       | string              | e.g., `"tax"`, `"service"`         |
| `name`       | string              | Display name                       |
| `amount`     | decimal             |                                    |
| `created_at` | datetime (ISO 8601) |                                    |

### SplitBillParticipantResponse

| Field          | Type                | Notes                                    |
| -------------- | ------------------- | ---------------------------------------- |
| `id`           | integer             |                                          |
| `name`         | string              |                                          |
| `is_payer`     | boolean             |                                          |
| `paid_amount`  | decimal             | How much this person actually paid       |
| `final_amount` | decimal             | How much this person owes (their share)  |
| `created_at`   | datetime (ISO 8601) |                                          |

### SplitBillParticipantDetailResponse

Extends `SplitBillParticipantResponse` with:

| Field   | Type                                   | Notes |
| ------- | -------------------------------------- | ----- |
| `items` | list[SplitBillParticipantItemResponse] | Empty for equal/custom split mode |

### SplitBillParticipantItemResponse

| Field                | Type    | Notes |
| -------------------- | ------- | ----- |
| `item_id`            | integer |       |
| `item_name`          | string  |       |
| `portion`            | integer | Portion value used in item-based split |
| `allocated_subtotal` | decimal | Subtotal assigned to participant for this item |

### SplitBillDebtResponse

| Field                    | Type                | Notes                                   |
| ------------------------ | ------------------- | --------------------------------------- |
| `id`                     | integer             |                                         |
| `debtor_participant_id`  | integer             | Participant who owes money              |
| `creditor_participant_id`| integer             | Participant who is owed money           |
| `amount`                 | decimal             | Original debt amount                    |
| `remaining_amount`       | decimal             | Remaining unpaid amount                 |
| `is_settled`             | boolean             | `true` when `remaining_amount` is `0`   |
| `created_at`             | datetime (ISO 8601) |                                         |

### SplitBillSettlementResponse

| Field                  | Type                | Notes                             |
| ---------------------- | ------------------- | --------------------------------- |
| `id`                   | integer             |                                   |
| `debt_id`              | integer             |                                   |
| `from_participant_id`  | integer             | Participant who made the payment  |
| `to_participant_id`    | integer             | Participant who received payment  |
| `amount`               | decimal             |                                   |
| `created_at`           | datetime (ISO 8601) |                                   |

### SplitBillSettlementSummaryResponse

| Field                   | Type    | Notes |
| ----------------------- | ------- | ----- |
| `total_debt_amount`     | decimal | Sum of debt amounts |
| `remaining_debt_amount` | decimal | Sum of remaining unpaid debt |
| `settled_debt_count`    | integer | Count of debts with `is_settled=true` |
| `total_debt_count`      | integer | Total debt rows |
| `settlement_count`      | integer | Number of settlement rows |
| `settled_amount`        | decimal | `total_debt_amount - remaining_debt_amount` |

### SplitBillCalculateResponse

| Field          | Type                              | Notes                                          |
| -------------- | --------------------------------- | ---------------------------------------------- |
| `title`        | string                            |                                                |
| `total_amount` | decimal                           |                                                |
| `participants` | list[SplitBillParticipantResponse]|                                                |
| `debts`        | list[SplitBillDebtResponse]       |                                                |
| `summary`      | list[DebtSummary]                 | Human-readable per-debt breakdown              |
| `text`         | string                            | Plain-text summary of who owes whom            |

### DebtSummary

| Field           | Type                  | Notes                                  |
| --------------- | --------------------- | -------------------------------------- |
| `debtor_name`   | string                |                                        |
| `creditor_name` | string                |                                        |
| `amount`        | decimal               |                                        |
| `items`         | list[DebtSummaryItem] | Items that contributed to this debt    |

### RecurringCreate

| Field             | Type               | Required | Default | Notes                                                        |
| ----------------- | ------------------ | -------- | ------- | ------------------------------------------------------------ |
| `account_id`      | integer            | Yes      | -       |                                                              |
| `category_id`     | integer or null    | No       | `null`  | Must match transaction `type`                                |
| `type`            | TransactionType    | Yes      | -       |                                                              |
| `amount`          | decimal            | Yes      | -       | `> 0`, max 2 decimal places                                  |
| `frequency`       | RecurringFrequency | Yes      | -       | See [Enum Reference](#9-enum-reference)                      |
| `day_of_week`     | integer or null    | Conditional | `null` | 0-6. Required for `weekly`.                                 |
| `day_of_month`    | integer or null    | Conditional | `null` | 1-31. Required for `monthly`/`yearly`.                      |
| `month_of_year`   | integer or null    | Conditional | `null` | 1-12. Required for `yearly`.                                |
| `start_date`      | date (YYYY-MM-DD)  | Yes      | -       |                                                              |
| `end_date`        | date or null       | No       | `null`  | Must be after `start_date`                                   |
| `timezone`        | string             | No       | `"UTC"` | IANA timezone                                                |
| `auto_create`     | boolean            | No       | `true`  |                                                              |
| `max_occurrences` | integer or null    | No       | `null`  | Min `1`                                                      |
| `note`            | string or null     | No       | `null`  | Max 500 chars; whitespace stripped                           |

### RecurringUpdate

| Field             | Type           | Notes                                      |
| ----------------- | -------------- | ------------------------------------------ |
| `category_id`     | integer or null | Must match original transaction type      |
| `amount`          | decimal or null | `> 0`, max 2 decimal places               |
| `end_date`        | date or null   |                                            |
| `timezone`        | string or null | IANA timezone                              |
| `auto_create`     | boolean or null |                                           |
| `max_occurrences` | integer or null | Min `1`                                   |
| `is_active`       | boolean or null |                                           |
| `note`            | string or null | Max 500 chars; whitespace stripped         |

### RecurringSummary

| Field                      | Type    | Notes                                                                            |
| -------------------------- | ------- | -------------------------------------------------------------------------------- |
| `total_monthly_income`     | decimal | Monthly-equivalent sum of active recurring `income` templates                    |
| `total_monthly_expense`    | decimal | Monthly-equivalent sum of active recurring `expense` templates                   |
| `net_monthly_commitment`   | decimal | `total_monthly_income - total_monthly_expense`                                   |

### RecurringResponse

| Field              | Type                | Notes                                                  |
| ------------------ | ------------------- | ------------------------------------------------------ |
| `id`               | integer             |                                                        |
| `account_id`       | integer             |                                                        |
| `category_id`      | integer or null     |                                                        |
| `type`             | TransactionType     |                                                        |
| `amount`           | decimal             |                                                        |
| `frequency`        | RecurringFrequency  |                                                        |
| `day_of_week`      | integer or null     |                                                        |
| `day_of_month`     | integer or null     |                                                        |
| `month_of_year`    | integer or null     |                                                        |
| `start_date`       | date (YYYY-MM-DD)   |                                                        |
| `end_date`         | date or null        |                                                        |
| `next_due_date`    | date (YYYY-MM-DD)   | Next scheduled execution date                          |
| `last_run_at`      | datetime or null    | Timestamp of last execution                            |
| `timezone`         | string              |                                                        |
| `auto_create`      | boolean             |                                                        |
| `max_occurrences`  | integer or null     |                                                        |
| `occurrence_count` | integer             | Number of times this template has been executed        |
| `is_active`        | boolean             |                                                        |
| `note`             | string or null      |                                                        |
| `created_at`       | datetime (ISO 8601) |                                                        |
| `updated_at`       | datetime (ISO 8601) |                                                        |

### OverviewResponse

| Field               | Type           | Notes                                                     |
| ------------------- | -------------- | --------------------------------------------------------- |
| `total_income`      | decimal        | Sum of income in current period                           |
| `total_expense`     | decimal        | Sum of expense in current period                          |
| `net`               | decimal        | `total_income - total_expense`                            |
| `transaction_count` | integer        | Number of matching transactions in current period         |
| `savings_rate`      | decimal or null| `net / total_income * 100`, rounded 2 decimals, null if income=0 |
| `previous_period`   | OverviewPeriod | Previous-period totals (same duration)                    |
| `delta`             | OverviewDelta  | Difference between current and previous period            |

### CashflowTrendItem

| Field            | Type              | Notes                                              |
| ---------------- | ----------------- | -------------------------------------------------- |
| `period`         | string            | `YYYY-MM-DD`, `YYYY-Www`, or `YYYY-MM`             |
| `start_date`     | date (YYYY-MM-DD) | Bucket start boundary                              |
| `end_date`       | date (YYYY-MM-DD) | Bucket end boundary                                |
| `income`         | decimal           | Income amount for bucket                           |
| `expense`        | decimal           | Expense amount for bucket                          |
| `net`            | decimal           | `income - expense`                                 |
| `cumulative_net` | decimal           | Running sum from the first bucket in range         |

### CategoryBreakdownResponse

| Field          | Type                          | Notes                               |
| -------------- | ----------------------------- | ----------------------------------- |
| `total_amount` | decimal                       | Total amount across all categories  |
| `items`        | list[CategoryBreakdownItem]   | Top categories by amount            |

### CategoryBreakdownItem

| Field               | Type            | Notes                                         |
| ------------------- | --------------- | --------------------------------------------- |
| `category_id`       | integer or null | `null` means Uncategorized                    |
| `name`              | string          | Category name                                 |
| `color`             | string          | Category color (`#RRGGBB`)                    |
| `icon`              | string          | Category icon token                           |
| `amount`            | decimal         | Total amount for this category                |
| `percentage`        | decimal or null | Percentage over total amount (rounded 2 dp)   |
| `transaction_count` | integer         | Number of transactions in this category       |

### AccountBreakdownItem

| Field               | Type        | Notes                                     |
| ------------------- | ----------- | ----------------------------------------- |
| `account_id`        | integer     |                                           |
| `account_name`      | string      |                                           |
| `account_type`      | AccountType | See [Enum Reference](#9-enum-reference)   |
| `amount`            | decimal     | Total amount for account                  |
| `percentage`        | decimal or null | Percentage over total amount          |
| `transaction_count` | integer     | Number of matching transactions           |

### TopTransactionItem

| Field            | Type              | Notes                                |
| ---------------- | ----------------- | ------------------------------------ |
| `transaction_id` | integer           |                                      |
| `date`           | date (YYYY-MM-DD) |                                      |
| `amount`         | decimal           |                                      |
| `account`        | string            | Account name                         |
| `category`       | string            | Category name or `Uncategorized`     |
| `note`           | string or null    |                                      |

### PeriodComparisonResponse

| Field             | Type                   | Notes                                 |
| ----------------- | ---------------------- | ------------------------------------- |
| `current_period`  | PeriodComparisonPeriod | Metrics for requested period          |
| `previous_period` | PeriodComparisonPeriod | Metrics for previous equal duration   |
| `delta`           | PeriodComparisonDelta  | Amount and percent differences        |

---

## 10. Enum Reference

### AccountType

| Value          | Category  | Description                                |
| -------------- | --------- | ------------------------------------------ |
| `cash`         | Asset     | Physical cash on hand                      |
| `bank_account` | Asset     | Bank savings or checking account           |
| `e_wallet`     | Asset     | Digital wallet (e.g., GoPay, OVO, Dana)    |
| `credit_card`  | Liability | Credit card; balance represents money owed |

Asset accounts (`cash`, `bank_account`, `e_wallet`) contribute to `total_assets` in the financial summary. `credit_card` accounts contribute to `total_liabilities`.

### TransactionType

| Value     | Description                                |
| --------- | ------------------------------------------ |
| `income`  | Money received (increases account balance) |
| `expense` | Money spent (decreases account balance)    |

### CategoryType

| Value     | Description                       |
| --------- | --------------------------------- |
| `income`  | Category for income transactions  |
| `expense` | Category for expense transactions |

### ReportGroupBy

| Value   | Description                                |
| ------- | ------------------------------------------ |
| `day`   | One point per day (`YYYY-MM-DD`)           |
| `week`  | One point per ISO week (`YYYY-Www`)        |
| `month` | One point per calendar month (`YYYY-MM`)   |

### RecurringFrequency

| Value     | Description                            | Required fields                          |
| --------- | -------------------------------------- | ---------------------------------------- |
| `daily`   | Executes every day                     | None                                     |
| `weekly`  | Executes on a specific day each week   | `day_of_week`                            |
| `monthly` | Executes on a specific day each month  | `day_of_month`                           |
| `yearly`  | Executes once a year                   | `day_of_month`, `month_of_year`          |

---

## 11. Error Reference

All error responses follow this structure:

```json
{
  "detail": "Error message here"
}
```

Validation errors from Pydantic (422) return a structured array:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": { "min_length": 1 }
    }
  ]
}
```

### Common HTTP Status Codes

| Code                     | Meaning               | Typical Cause                                               |
| ------------------------ | --------------------- | ----------------------------------------------------------- |
| 200 OK                   | Success               | Request completed successfully                              |
| 201 Created              | Resource created      | New user or account was created                             |
| 401 Unauthorized         | Authentication failed | Token missing, expired, or invalid                          |
| 403 Forbidden            | Authorization failed  | Authenticated but not permitted to access the resource      |
| 404 Not Found            | Resource not found    | The requested account ID does not exist or has been deleted |
| 409 Conflict             | Duplicate resource    | Email or account `(name, type)` already exists              |
| 422 Unprocessable Entity | Validation failed     | Request body did not pass schema validation                 |

