# Pocketree API Documentation

**Version:** 1.0.0

A personal finance management API for tracking accounts, transactions, and categories.

---

## Table of Contents

1. [Authentication Overview](#1-authentication-overview)
2. [Auth Endpoints](#2-auth-endpoints)
   - [POST /auth/register](#post-authregister)
   - [POST /auth/login](#post-authlogin)
   - [POST /auth/refresh](#post-authrefresh)
   - [POST /auth/logout](#post-authlogout)
   - [GET /auth/me](#get-authme)
3. [Accounts Endpoints](#3-accounts-endpoints)
   - [POST /accounts](#post-accounts)
   - [GET /accounts](#get-accounts)
   - [GET /accounts/summary](#get-accountssummary)
   - [GET /accounts/{account_id}](#get-accountsaccount_id)
   - [PUT /accounts/{account_id}](#put-accountsaccount_id)
   - [DELETE /accounts/{account_id}](#delete-accountsaccount_id)
4. [Transactions Endpoints](#4-transactions-endpoints)
   - [POST /transactions](#post-transactions)
   - [GET /transactions](#get-transactions)
   - [GET /transactions/summary](#get-transactionssummary)
   - [POST /transactions/transfer](#post-transactionstransfer)
   - [GET /transactions/{transaction_id}](#get-transactionstransaction_id)
   - [PUT /transactions/{transaction_id}](#put-transactionstransaction_id)
   - [DELETE /transactions/{transaction_id}](#delete-transactionstransaction_id)
5. [Schema Reference](#5-schema-reference)
6. [Enum Reference](#6-enum-reference)
7. [Error Reference](#7-error-reference)

---

## 1. Authentication Overview

Pocketree uses JWT Bearer tokens for authentication. Every request to a protected endpoint must include a valid access token in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

### Token Details

| Token | Expiry | Algorithm |
|---|---|---|
| Access token | 60 minutes | HS256 |
| Refresh token | 1 day | HS256 |

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

1. Call `POST /auth/register` or `POST /auth/login` to receive both tokens.
2. Use the `access_token` in the `Authorization` header for all protected endpoints.
3. When the access token expires (HTTP 401), call `POST /auth/refresh` with the `refresh_token` to get a new token pair.
4. Call `POST /auth/logout` to end the session client-side.

> **Note:** The API does not maintain a server-side token blocklist. Logout is a client-side operation — discard both tokens on the client after calling logout.

---

## 2. Auth Endpoints

### POST /auth/register

Registers a new user and returns a token pair. A default **Cash** account is automatically created for the new user.

- **Auth required:** No

**Request Body**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `name` | string | Yes | Non-empty |
| `email` | string (email) | Yes | Valid email format, must be unique |
| `password` | string | Yes | Min 8 chars; must contain uppercase, lowercase, digit, and special character (`!@#$%^&*()_-+=[]{}; :,.<>/?`) |

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "Secure@123"
}
```

**Response — 201 Created**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**

| Status | Detail | Cause |
|---|---|---|
| 409 Conflict | `Email already registered` | Email is already in use |
| 422 Unprocessable Entity | Validation error detail | Invalid email format or password does not meet requirements |

---

### POST /auth/login

Authenticates an existing user and returns a token pair.

- **Auth required:** No

**Request Body**

| Field | Type | Required |
|---|---|---|
| `email` | string (email) | Yes |
| `password` | string | Yes |

```json
{
  "email": "jane@example.com",
  "password": "Secure@123"
}
```

**Response — 200 OK**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid email or password` | Credentials do not match any user |

---

### POST /auth/refresh

Issues a new access token and refresh token using a valid, unexpired refresh token.

- **Auth required:** No (refresh token provided in body)

**Request Body**

| Field | Type | Required |
|---|---|---|
| `refresh_token` | string | Yes |

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response — 200 OK**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired refresh token` | Token is malformed, expired, or is not a refresh token |
| 401 Unauthorized | `User not found` | The user referenced by the token no longer exists |

---

### POST /auth/logout

Ends the current session. The server validates the token but does not blocklist it. Discard both tokens on the client after calling this endpoint.

- **Auth required:** Yes (Bearer access token)

**Request Body:** None

**Response — 200 OK**

```json
{
  "message": "Successfully logged out"
}
```

**Error Responses**

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Token is missing, malformed, or expired |

---

### GET /auth/me

Returns the profile of the currently authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body:** None

**Response — 200 OK**

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

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Token is missing, malformed, or expired |
| 401 Unauthorized | `User not found` | The user referenced by the token no longer exists |

---

## 3. Accounts Endpoints

All accounts endpoints require a valid Bearer access token. Accounts are scoped to the authenticated user — a user can only read and modify their own accounts.

Accounts are **soft-deleted**: deleting an account sets an `is_deleted` flag rather than removing the record. Soft-deleted accounts are excluded from all list and lookup responses. The uniqueness constraint on `(name, type)` applies only to active accounts, so a deleted account's name/type combination can be reused.

---

### POST /accounts

Creates a new account for the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `name` | string | Yes | 1–100 characters. Leading/trailing whitespace and consecutive internal spaces are normalized. |
| `type` | AccountType | Yes | One of: `cash`, `bank_account`, `e_wallet`, `credit_card` |
| `initial_balance` | decimal | No | Default `0.00`. Must be `>= 0.00`, max 2 decimal places. |

> The combination of `name` (case-insensitive) and `type` must be unique among the user's active accounts.

```json
{
  "name": "BCA Savings",
  "type": "bank_account",
  "initial_balance": "1500000.00"
}
```

**Response — 201 Created**

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

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 409 Conflict | `An active account with the same name and type already exists.` | Duplicate `(name, type)` for this user |
| 422 Unprocessable Entity | Validation error detail | Invalid field values (e.g., negative balance, name too long) |

---

### GET /accounts

Returns all active accounts belonging to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body:** None

**Response — 200 OK**

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

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /accounts/summary

Returns an aggregated financial summary across all active accounts for the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Account classification:**
- **Assets** (`total_assets`): `cash`, `bank_account`, `e_wallet`
- **Liabilities** (`total_liabilities`): `credit_card`
- **Net worth** = `total_assets` − `total_liabilities`

**Request Body:** None

**Response — 200 OK**

```json
{
  "total_assets": "1500000.00",
  "total_liabilities": "250000.00",
  "net_worth": "1250000.00",
  "accounts_count": 3
}
```

**Error Responses**

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /accounts/{account_id}

Returns a single active account by ID. The account must belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `account_id` | integer | The ID of the account |

**Response — 200 OK**

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

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 403 Forbidden | `Not authorized to access this account` | Account exists but belongs to another user |
| 404 Not Found | `Account not found` | No active account with this ID exists |

---

### PUT /accounts/{account_id}

Updates the name and/or type of an existing account. Fields not included in the request body are left unchanged. The account must belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `account_id` | integer | The ID of the account to update |

**Request Body**

All fields are optional.

| Field | Type | Constraints |
|---|---|---|
| `name` | string or null | 1–100 characters if provided. Whitespace is normalized. |
| `type` | AccountType or null | One of: `cash`, `bank_account`, `e_wallet`, `credit_card` |

> The resulting `(name, type)` combination must remain unique among the user's active accounts, excluding the account being updated.

```json
{
  "name": "BCA Main",
  "type": "bank_account"
}
```

**Response — 200 OK**

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

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 403 Forbidden | `Not authorized to access this account` | Account belongs to another user |
| 404 Not Found | `Account not found` | No active account with this ID exists |
| 409 Conflict | `An active account with the same name and type already exists.` | Updated `(name, type)` conflicts with another active account |
| 422 Unprocessable Entity | Validation error detail | Invalid field values |

---

### DELETE /accounts/{account_id}

Soft-deletes an account. The account is marked as deleted and excluded from all future responses. The account must belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `account_id` | integer | The ID of the account to delete |

**Request Body:** None

**Response — 200 OK**

```json
{
  "message": "Account deleted successfully"
}
```

**Error Responses**

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 403 Forbidden | `Not authorized to access this account` | Account belongs to another user |
| 404 Not Found | `Account not found` | No active account with this ID exists |

---

## 4. Transactions Endpoints

All transactions endpoints require a valid Bearer access token. Transactions are scoped to the authenticated user.

Transactions are **soft-deleted**: deleting a transaction sets an `is_deleted` flag. Transfer transactions come in pairs — deleting one automatically deletes its paired counterpart.

---

### POST /transactions

Creates a new income or expense transaction for the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `account_id` | integer | Yes | Must belong to the authenticated user |
| `category_id` | integer or null | No | Must exist and match the transaction `type` |
| `type` | TransactionType | Yes | `income` or `expense` |
| `amount` | decimal | Yes | `> 0`, max 2 decimal places |
| `date` | date (YYYY-MM-DD) | Yes | |
| `note` | string or null | No | Max 500 characters; leading/trailing whitespace stripped |

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

**Response — 201 Created**

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

| Status | Detail | Cause |
|---|---|---|
| 400 Bad Request | `Category type '...' does not match transaction type '...'` | Category type conflicts with transaction type |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 404 Not Found | `Account not found` | Account does not exist or belongs to another user |
| 404 Not Found | `Category not found` | Category does not exist or belongs to another user |
| 422 Unprocessable Entity | Validation error detail | Invalid field values |

---

### GET /transactions

Returns a paginated list of the authenticated user's transactions. Supports filtering and pagination via query parameters.

- **Auth required:** Yes (Bearer access token)

**Query Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `account_id` | integer | — | Filter by account |
| `category_id` | integer | — | Filter by category |
| `type` | TransactionType | — | Filter by `income` or `expense` |
| `start_date` | date (YYYY-MM-DD) | — | Transactions on or after this date |
| `end_date` | date (YYYY-MM-DD) | — | Transactions on or before this date |
| `limit` | integer | `20` | Results per page (1–100) |
| `offset` | integer | `0` | Number of results to skip |

**Request Body:** None

**Response — 200 OK**

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

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### GET /transactions/summary

Returns an aggregated income/expense summary for the authenticated user, optionally filtered.

- **Auth required:** Yes (Bearer access token)

**Query Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `account_id` | integer | — | Summary for a specific account |
| `category_id` | integer | — | Summary for a specific category |
| `date_from` | date (YYYY-MM-DD) | — | Start date (inclusive) |
| `date_to` | date (YYYY-MM-DD) | — | End date (inclusive) |

**Request Body:** None

**Response — 200 OK**

```json
{
  "total_income": "500000.00",
  "total_expense": "150000.00",
  "net": "350000.00",
  "transaction_count": 12
}
```

**Error Responses**

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |

---

### POST /transactions/transfer

Creates a transfer between two of the authenticated user's accounts. This creates a linked pair of transactions (one `expense` on the source, one `income` on the destination).

- **Auth required:** Yes (Bearer access token)

**Request Body**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `from_account_id` | integer | Yes | Source account; must belong to the authenticated user |
| `to_account_id` | integer | Yes | Destination account; must be different from `from_account_id` |
| `amount` | decimal | Yes | `> 0`, max 2 decimal places |
| `date` | date (YYYY-MM-DD) | Yes | |
| `note` | string or null | No | Max 500 characters; leading/trailing whitespace stripped |

```json
{
  "from_account_id": 1,
  "to_account_id": 7,
  "amount": "200000.00",
  "date": "2026-03-22",
  "note": "Top up savings"
}
```

**Response — 201 Created**

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

| Status | Detail | Cause |
|---|---|---|
| 400 Bad Request | `Transfer failed. Please check your accounts.` | Database integrity error during transfer |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 404 Not Found | `Source account not found` | `from_account_id` does not exist or belongs to another user |
| 404 Not Found | `Destination account not found` | `to_account_id` does not exist or belongs to another user |
| 422 Unprocessable Entity | `Cannot transfer to the same account` | `from_account_id` and `to_account_id` are the same |

---

### GET /transactions/{transaction_id}

Returns a single transaction by ID. The transaction must belong to the authenticated user.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `transaction_id` | integer | The ID of the transaction |

**Request Body:** None

**Response — 200 OK**

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

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 403 Forbidden | `Not authorized to access this transaction` | Transaction belongs to another user |
| 404 Not Found | `Transaction not found` | No active transaction with this ID exists |

---

### PUT /transactions/{transaction_id}

Updates a transaction. Transfer transactions cannot be modified — delete and recreate instead. All fields are optional; omitted fields are left unchanged.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `transaction_id` | integer | The ID of the transaction to update |

**Request Body**

All fields are optional.

| Field | Type | Constraints |
|---|---|---|
| `category_id` | integer or null | Must exist and match the original transaction type |
| `amount` | decimal or null | `> 0`, max 2 decimal places |
| `date` | date (YYYY-MM-DD) or null | |
| `note` | string or null | Max 500 characters; leading/trailing whitespace stripped |

```json
{
  "amount": "75000.00",
  "note": "Dinner"
}
```

**Response — 200 OK**

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

| Status | Detail | Cause |
|---|---|---|
| 400 Bad Request | `Category type '...' does not match transaction type '...'` | Category type conflicts with original transaction type |
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 403 Forbidden | `Not authorized to access this transaction` | Transaction belongs to another user |
| 403 Forbidden | `Transfer transactions cannot be modified. Delete the transfer and create a new one.` | Transaction is part of a transfer pair |
| 404 Not Found | `Transaction not found` | No active transaction with this ID exists |
| 404 Not Found | `Category not found` | Category does not exist or belongs to another user |
| 422 Unprocessable Entity | Validation error detail | Invalid field values |

---

### DELETE /transactions/{transaction_id}

Soft-deletes a transaction. If the transaction is part of a transfer pair, the paired transaction is also deleted.

- **Auth required:** Yes (Bearer access token)

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `transaction_id` | integer | The ID of the transaction to delete |

**Request Body:** None

**Response — 200 OK**

```json
{
  "message": "Transaction deleted successfully"
}
```

**Error Responses**

| Status | Detail | Cause |
|---|---|---|
| 401 Unauthorized | `Invalid or expired token` | Missing or invalid Bearer token |
| 403 Forbidden | `Not authorized to access this transaction` | Transaction belongs to another user |
| 404 Not Found | `Transaction not found` | No active transaction with this ID exists |

---

## 5. Schema Reference

### UserRegister

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | User's display name |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Min 8 chars; must include uppercase, lowercase, digit, and special character |

### UserLogin

| Field | Type | Required |
|---|---|---|
| `email` | string | Yes |
| `password` | string | Yes |

### TokenRefresh

| Field | Type | Required |
|---|---|---|
| `refresh_token` | string | Yes |

### AccountCreate

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `name` | string | Yes | — | 1–100 chars; whitespace is normalized |
| `type` | AccountType | Yes | — | See [Enum Reference](#5-enum-reference) |
| `initial_balance` | decimal | No | `0.00` | Must be `>= 0.00`; max 2 decimal places |

### AccountUpdate

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string or null | No | 1–100 chars if provided; whitespace is normalized |
| `type` | AccountType or null | No | See [Enum Reference](#5-enum-reference) |

### TokenResponse

| Field | Type | Notes |
|---|---|---|
| `access_token` | string | JWT; valid for 60 minutes |
| `refresh_token` | string | JWT; valid for 1 day |
| `token_type` | string | Always `"bearer"` |

### UserResponse

| Field | Type |
|---|---|
| `id` | integer |
| `name` | string |
| `email` | string |
| `created_at` | datetime (ISO 8601) |
| `updated_at` | datetime (ISO 8601) |

### MessageResponse

| Field | Type |
|---|---|
| `message` | string |

### AccountResponse

| Field | Type | Notes |
|---|---|---|
| `id` | integer | |
| `name` | string | |
| `type` | AccountType | |
| `balance` | decimal | Current balance, updated by transactions |
| `initial_balance` | decimal | Starting balance set at creation |
| `created_at` | datetime (ISO 8601) | |
| `updated_at` | datetime (ISO 8601) | |

### AccountSummary

| Field | Type | Notes |
|---|---|---|
| `total_assets` | decimal | Sum of balances for `cash`, `bank_account`, `e_wallet` accounts |
| `total_liabilities` | decimal | Sum of balances for `credit_card` accounts |
| `net_worth` | decimal | `total_assets` − `total_liabilities` |
| `accounts_count` | integer | Total number of active accounts |

### TransactionCreate

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `account_id` | integer | Yes | — | Must belong to the authenticated user |
| `category_id` | integer or null | No | `null` | Must exist and match transaction `type` |
| `type` | TransactionType | Yes | — | See [Enum Reference](#6-enum-reference) |
| `amount` | decimal | Yes | — | `> 0`, max 2 decimal places |
| `date` | date (YYYY-MM-DD) | Yes | — | |
| `note` | string or null | No | `null` | Max 500 chars; whitespace stripped |

### TransactionUpdate

| Field | Type | Required | Notes |
|---|---|---|---|
| `category_id` | integer or null | No | Must exist and match original transaction type |
| `amount` | decimal or null | No | `> 0`, max 2 decimal places |
| `date` | date (YYYY-MM-DD) or null | No | |
| `note` | string or null | No | Max 500 chars; whitespace stripped |

### TransactionTransfer

| Field | Type | Required | Notes |
|---|---|---|---|
| `from_account_id` | integer | Yes | Source account; must belong to the authenticated user |
| `to_account_id` | integer | Yes | Destination account; must differ from `from_account_id` |
| `amount` | decimal | Yes | `> 0`, max 2 decimal places |
| `date` | date (YYYY-MM-DD) | Yes | |
| `note` | string or null | No | Max 500 chars; whitespace stripped |

### TransactionResponse

| Field | Type | Notes |
|---|---|---|
| `id` | integer | |
| `account_id` | integer | |
| `category_id` | integer or null | |
| `type` | TransactionType | `income` or `expense` |
| `amount` | decimal | |
| `date` | date (YYYY-MM-DD) | |
| `note` | string or null | |
| `transfer_id` | integer or null | ID of the paired transaction if part of a transfer |
| `created_at` | datetime (ISO 8601) | |
| `updated_at` | datetime (ISO 8601) | |

### TransferResponse

| Field | Type | Notes |
|---|---|---|
| `from_transaction` | TransactionResponse | The outgoing (expense) side of the transfer |
| `to_transaction` | TransactionResponse | The incoming (income) side of the transfer |
| `message` | string | Always `"Transfer completed successfully"` |

### TransactionSummary

| Field | Type | Notes |
|---|---|---|
| `total_income` | decimal | Sum of all income transactions matching the filter |
| `total_expense` | decimal | Sum of all expense transactions matching the filter |
| `net` | decimal | `total_income` − `total_expense` |
| `transaction_count` | integer | Total number of matching transactions |

---

## 6. Enum Reference

### AccountType

| Value | Category | Description |
|---|---|---|
| `cash` | Asset | Physical cash on hand |
| `bank_account` | Asset | Bank savings or checking account |
| `e_wallet` | Asset | Digital wallet (e.g., GoPay, OVO, Dana) |
| `credit_card` | Liability | Credit card; balance represents money owed |

Asset accounts (`cash`, `bank_account`, `e_wallet`) contribute to `total_assets` in the financial summary. `credit_card` accounts contribute to `total_liabilities`.

### TransactionType

| Value | Description |
|---|---|
| `income` | Money received (increases account balance) |
| `expense` | Money spent (decreases account balance) |

---

## 7. Error Reference

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

| Code | Meaning | Typical Cause |
|---|---|---|
| 200 OK | Success | Request completed successfully |
| 201 Created | Resource created | New user or account was created |
| 401 Unauthorized | Authentication failed | Token missing, expired, or invalid |
| 403 Forbidden | Authorization failed | Authenticated but not permitted to access the resource |
| 404 Not Found | Resource not found | The requested account ID does not exist or has been deleted |
| 409 Conflict | Duplicate resource | Email or account `(name, type)` already exists |
| 422 Unprocessable Entity | Validation failed | Request body did not pass schema validation |
