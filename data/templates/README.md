# Templates Directory

This directory stores user-created templates for DealGenie Pro.

## Template Structure

Each template is saved as a JSON file with the following structure:

```json
{
  "template_name": "Template Name",
  "created_date": "2025-10-01T12:00:00",
  "benchmark_overrides": {
    "asset_class": {
      "subclass": {
        "metric_name": [min, preferred, max, "source"]
      }
    }
  },
  "custom_dd_items": {},
  "profile_name": "User or Company Name"
}
```

## Usage

- Templates are created and managed through the sidebar in the DealGenie Pro application
- Save your current benchmark overrides and settings as a template
- Load previously saved templates to quickly apply settings
- Templates are stored locally and not tracked in git (for privacy)

## Note

Template files (*.json) are ignored by git to protect user data privacy. Only the directory structure (.gitkeep) is tracked in version control.
