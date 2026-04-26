from datetime import datetime, timezone

print('autoclaw_time utc=' + datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
