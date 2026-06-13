# TP5 - HTTP Communication

## Objective

This TP explains basic communication between a client and a server using HTTP in Python.

It includes:

- A simple HTTP server
- A client with timeout
- A retry mechanism
- Asynchronous service calls

## Files

- `resource_server.py`: starts a local HTTP server.
- `resource_client.py`: sends requests to the server with timeout.

## Concepts Used

- HTTP server
- JSON response
- Timeout
- Client-server communication
- Network latency simulation

## How to Run

First, start the server:

```bash
python resource_server.py