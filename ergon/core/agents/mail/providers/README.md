# Mail Provider Adapters

This directory was created as part of refactoring the large `providers.py` file into a more modular structure to improve maintainability and readability, following the Tekton engineering guidelines on file size (under 500 lines per file).

## Module Structure

The providers are organized into separate files:

- `base.py`: Contains the abstract base class for mail providers
- `gmail.py`: Gmail implementation of the mail provider interface
- `outlook.py`: Outlook/Microsoft 365 implementation of the mail provider interface
- `__init__.py`: Exports the provider classes and factory function

## Compatibility

The original `providers.py` file acts as a compatibility layer, re-exporting the key components from the modular structure. This ensures backward compatibility with existing code that imports from the original location.

## Usage

The functionality remains the same, but the code is now more modular and easier to maintain. Import the classes and functions as before:

```python
from ergon.core.agents.mail.providers import MailProvider, GmailProvider, OutlookProvider, get_mail_provider
```

Or import directly from the new structure:

```python
from ergon.core.agents.mail.providers.base import MailProvider
from ergon.core.agents.mail.providers.gmail import GmailProvider
from ergon.core.agents.mail.providers.outlook import OutlookProvider
from ergon.core.agents.mail.providers import get_mail_provider
```