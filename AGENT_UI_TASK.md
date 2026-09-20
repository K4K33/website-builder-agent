# Task: Build the Website Builder Agent UI

We now need to build the first user interface for the Website Builder Agent.

## Goal

Create a simple, professional web application that allows the user to communicate with the Website Builder Agent through a chat interface.

The UI should eventually work both on desktop and mobile. Build it as a responsive web app/PWA foundation so it can later be installed on a phone like an app.

## Important project requirements

- Inspect the existing project before changing anything.
- Preserve all existing functionality.
- Do not break the existing Research → Build → QA → Publish pipeline.
- Do not remove existing commands or files unless they are genuinely obsolete.
- Do not purchase or require any paid service.
- Do not unnecessarily call OpenRouter or Tavily while developing the UI.
- Prefer local/mock functionality for UI testing.
- Do not expose API keys in frontend code.
- Do not invent company information.
- Keep the architecture simple and maintainable.

## User experience

Create a clean chat interface with:

- Kaurivo / Website Builder Agent branding
- conversation area
- user messages
- agent messages
- text input
- Send button
- loading state
- clear error state
- responsive mobile layout
- responsive desktop layout

The visual design should be:

- professional
- modern
- minimalist
- clean
- premium
- easy to use
- mobile-first

Avoid:

- excessive gradients
- unnecessary animations
- clutter
- fake statistics
- fake testimonials
- unnecessary UI elements

## Agent interaction

The UI must be designed so that the user can eventually send commands such as:

"Build Kaurivo's website."

"Find businesses with outdated websites."

"Show me today's projects."

"Show me the latest demo."

"Create an outreach draft for this company."

For the first version, it is acceptable to connect the chat to a local command/API layer rather than implementing a fully autonomous AI conversation system.

The important thing is to establish a clean architecture where the frontend can communicate with the existing Python agent backend.

## Backend/API

Inspect the existing Python project and determine the simplest safe way to expose agent functionality to the frontend.

Prefer a lightweight local web API.

Do not introduce unnecessary dependencies.

If a web framework is needed, use a lightweight and well-supported option.

Keep API keys and secrets strictly on the backend.

## PWA foundation

Prepare the application so that it can later become installable on a phone.

Include where appropriate:

- web app manifest
- mobile viewport configuration
- app name
- icons placeholder/configuration
- responsive layout

Do not spend time creating elaborate icons yet.

## Existing functionality

The existing project already contains functionality for:

- research
- website building
- QA
- publishing demos
- company/project state
- resource usage management

The UI should be designed around these existing capabilities rather than creating a completely separate system.

## Testing

Use local tests and mock responses wherever possible.

Do not consume OpenRouter or Tavily credits just to test the chat interface.

Verify at minimum:

1. frontend loads
2. chat UI renders
3. user can enter a message
4. message appears in conversation
5. backend/API connection works locally
6. errors are displayed cleanly
7. existing Python pipeline still works
8. mobile layout works

## Important

Do NOT automatically send outreach messages.

Do NOT purchase domains.

Do NOT send emails.

Do NOT make real customer contact.

Do NOT create fake reviews or testimonials.

## Deliverable

Build the first working version of the Website Builder Agent UI.

At the end, report:

1. files created
2. files modified
3. dependencies added
4. how to start the UI locally
5. how the frontend communicates with the backend
6. what existing agent commands are currently connected
7. what remains to be implemented
8. confirmation that no unnecessary external API calls were made
