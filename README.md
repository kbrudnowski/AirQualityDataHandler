# Air Quality Data Processor

A Python application for fetching air quality data from the OpenAQ API and processing it as a Google Cloud Function.

## Features

- Automatically determines city boundaries using external geocoding services
- Fetches latest measurement data for parameters: PM2.5, PM10, O3, NO2
- Handles data from multiple measurement stations for each city
- Validates data and handles errors
- Saves results in CSV format to Google Cloud Storage
- Implemented as a Google Cloud Function
- Ready for scheduled execution

## Requirements

- Python 3.9+
- OpenAQ account (free): https://openaq.org/
- Google Cloud Platform with enabled services

## Usage

### Function Invocation

After deployment, you'll receive a function URL in the format:
```
https://europe-west1-YOUR_PROJECT_ID.cloudfunctions.net/air-quality-processor
```

**Testing the function:**

```bash
# GET request (uses default cities: Warsaw, London, default bucket)
curl https://your-function-url

# POST request with custom cities and bucket
curl -X POST https://your-function-url \
  -H "Content-Type: application/json" \
  -d '{"cities": ["Warsaw", "London", "Berlin"], "bucket_name": "my-custom-bucket"}'

# POST request with custom bucket only
curl -X POST https://your-function-url \
  -H "Content-Type: application/json" \
  -d '{"bucket_name": "my-air-quality-data"}'
```

## Output Data Structure

The CSV file contains the following columns:
- `city_name`: City name
- `location_name`: Measurement station location
- `parameter_name`: Parameter (PM2.5, PM10, O3, NO2)
- `parameter_value`: Measurement value
- `parameter_unit`: Measurement unit
- `utc_ts`: Measurement time (UTC)

## License

MIT

