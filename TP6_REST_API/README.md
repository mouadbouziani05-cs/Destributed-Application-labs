
## `TP6_REST_API/README.md`

```md
# TP6 - REST API

## Objective

This TP shows how to build a small REST API using Python standard libraries.

The API manages support tickets with authentication and JSON validation.

## Files

- `api_server.py`: creates the REST API server.
- `api_client.py`: sends HTTP requests to the API.

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check if the API is running |
| POST | `/tickets` | Create a new ticket |

## Concepts Used

- REST API
- HTTP methods
- JSON body
- Token authentication
- Input validation
- HTTP status codes
- X-Request-Id for tracing

## How to Run

First, start the API server:

```bash
python api_server.py