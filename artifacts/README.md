# Submission Artifacts

This directory contains output artifacts generated during testing and verification.

## Files

| File | Description |
|------|-------------|
| `producer_output.log` | Terminal output from the producer showing Kafka acknowledgements |
| `consumer_output.log` | Terminal output from the consumer showing processed messages |
| `test_results.log` | Output from pytest test suite |

## Generating Artifacts

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Generate producer output
python src/producer.py --topics sales --limit 15 --interval 0.3 2>&1 | Tee-Object -FilePath artifacts/producer_output.log

# Generate consumer output  
python src/consumer.py --limit 15 2>&1 | Tee-Object -FilePath artifacts/consumer_output.log

# Run tests
pytest tests/ -v 2>&1 | Tee-Object -FilePath artifacts/test_results.log
```
