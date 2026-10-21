# Agent 19

| Field | Declared |
|---|---|
| Use | Airline customer service: bookings, changes, cancellations, baggage, refunds and compensation |
| Model | OpenAI gpt-6-luna (small tier) |
| Tools | get_user_details, get_reservation_details, search_direct_flight, search_onestop_flight, list_all_airports, get_flight_status, calculate (read and compute); book_reservation, cancel_reservation, update_reservation_flights, update_reservation_baggages, update_reservation_passengers, send_certificate (write; move money); transfer_to_human_agents |
| Money-moving tools enabled | Yes |
| Human approval before refunds or compensation | No |
| Guardrail | None declared |
| Policy document given to the agent | Airline policy, current revision |
| Volume assumption for pricing | Price per 1,000 conversations |
