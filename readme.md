# CampingCare Home Assistant Integration

## Overview
This integration allows you to connect to your CampingCare API to query guest information and booking data via license plate recognition.

## Installation via HACS:
1. Add the repository to your HACS integration.
2. Follow the setup instructions to configure the API key and base URL.

## Setup Instructions
1. Navigate to the Home Assistant Integrations page.
2. Search for "CampingCareHA" and click on the integration.
3. Enter your CampingCare API key and base URL when prompted.
4. Save the configuration.

## Example Usage
### Query License Plate
Once the integration is set up, you can use the `query_license_plate` service to fetch guest information. Example:

```yaml
service: campingcareha.query_license_plate
data:
  license_plate: "ABC123"
```

### Automations
You can create automations to trigger actions based on license plate recognition. Example:

```yaml
automation:
  - alias: Notify on Guest Arrival
    trigger:
      platform: event
      event_type: campingcareha.license_plate_recognized
      event_data:
        license_plate: "ABC123"
    action:
      - service: notify.mobile_app
        data:
          message: "Guest with license plate ABC123 has arrived."
```
