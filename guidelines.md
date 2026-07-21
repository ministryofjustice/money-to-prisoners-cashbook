# Digital Cashbook (Cashbook) Development Guidelines

## Project Overview and Core Functions

The Digital Cashbook is the site for prison staff (business hub) to manage prisoner money. It allows them to credit money to prisoners' accounts and manage disbursements (sending money out).

### Core Functionalities
- **New Credits Processing**: Review and process incoming money for prisoners.
- **Manual Credits**: Handle money that needs to be manually credited (e.g., from external sources).
- **Disbursements**: Create and manage requests for prisoners to send money out to external recipients (bank transfers, cheques, etc.).
- **Prisoner Search**: Look up prisoner information and their transaction history.
- **FAQ and Help**: Provide guidance to prison staff on using the system.

## Application Architecture

The project is built with **Django** and relies on the `money-to-prisoners-api` for its data and core business logic. It also integrates with HMPPS and Gov.UK external services for real-time data and notifications.

### Key Integrations
The application interacts with several APIs to fulfill its functionality:

- **MTP API (`money-to-prisoners-api`)**:
  - Central data store and authentication provider.
  - Staff sign in against it via OAuth2 (`mtp_common.auth.backends.MojBackend`); user accounts live in its database.
  - Used for processing credits, managing disbursements, and tracking transaction history.
- **HMPPS Prison API (NOMIS)**:
  - Fetches real-time prisoner location and status.
  - Used to verify that money is being sent to or from the correct prisoner.
- **HMPPS Auth**:
  - Issues a machine-to-machine token so the Prison API can be called. No user signs in through it.
- **GOV.UK Notify**:
  - Sends email notifications to staff and public users.
- **Postcode Lookup API**:
  - Used for address verification and lookup in the disbursement process.

### Key Project Apps
- **`cashbook` (`mtp_cashbook.apps.cashbook`)**: Core logic for processing credits and searching.
- **`disbursements` (`mtp_cashbook.apps.disbursements`)**: Logic for managing outgoing money.
- **`mtp_auth` (`mtp_cashbook.apps.mtp_auth`)**: Manages authentication and user permissions.
- **`mtp_common`**: A shared library used across all MTP projects for consistent styling, utilities, and common logic.

## Build and Configuration

- **Environment**: Requires Python 3.12+ and Node.js 24+.
- **Virtual Environment**: Use a Python virtual environment to isolate dependencies.
  ```shell
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Dependencies**: Managed via `run.py`. To update all dependencies:
  ```shell
  ./run.py dependencies
  ```
- **Configuration**:
  - The application connects to the API (default `http://localhost:8000`).
  - Local settings can be overridden in `mtp_cashbook/settings/local.py` (copy from `local.py.sample`).
- **Management Script**: `run.py` is the primary interface for development tasks.
  - `./run.py serve`: Start development server with live-reload (BrowserSync on `:3001`, Django on `:8001`).
  - `./run.py start`: Start development server without live-reload.
  - `./run.py --verbosity 2 help`: List all available build tasks.

## Access and Login

- **URL**: Once running, the application is accessible at [http://localhost:8001/](http://localhost:8001/).
- **API Requirement**: The `money-to-prisoners-api` must be running for the Cashbook to function.
- **Local Dev Login**: Use credentials `test-prison-1` or `test-prison-2` with the default password configured in your local API setup (usually `test-prison-1`).

### User Setup (in MTP API)
To allow a user to log into the Cashbook, they must be set up in the `money-to-prisoners-api` with the following:
1.  **Role**: `prison-clerk`.
2.  **Group**: `PrisonClerk`.
3.  **Application Mapping**: The user must be mapped to the `Digital cashbook` application (`cashbook` client ID).
4.  **Prison Mapping**: The user must be mapped to at least one prison (`PrisonUserMapping`) to see and process credits for that prison.

## Testing

### Running Tests
- **Full Suite**: Use `./run.py test`. This includes building assets and running Django tests.
- **Django Tests Only**: Run `manage.py test` directly:
  ```shell
  ./manage.py test cashbook
  ./manage.py test disbursements
  ```

## Additional Development Information

- **Frontend Assets**:
  - Assets are located in `mtp_cashbook/assets-src/`.
  - Built assets are placed in `mtp_cashbook/assets/`.
  - Use `./run.py build` to compile assets (SASS and JavaScript).
- **Translations**:
  - Update messages with `./run.py make_messages`.
- **Docker**:
  - Run with `./run.py local_docker` for a production-like environment.
- **Referenced Modules**:
  - `money-to-prisoners-common`: Shared components.
  - `django-zendesk-tickets`: For support ticket integration.
  - `django-moj-irat`: For incident reporting and tracking.
