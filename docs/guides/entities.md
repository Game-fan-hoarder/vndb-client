# Entities

Each entity has a typed Pydantic model and a query resource on the client:

| Resource            | Model       | VNDB endpoint |
| ------------------- | ----------- | ------------- |
| `client.vn`         | `VN`        | `/vn`         |
| `client.release`    | `Release`   | `/release`    |
| `client.producer`   | `Producer`  | `/producer`   |
| `client.character`  | `Character` | `/character`  |
| `client.staff`      | `Staff`     | `/staff`      |
| `client.tag`        | `Tag`       | `/tag`        |
| `client.trait`      | `Trait`     | `/trait`      |
| `client.quote`      | `Quote`     | `/quote`      |
| `client.ulist`      | `UlistEntry`| `/ulist`      |

All models are importable from the package root:

```python
from vndb_client import VN, Release, Character

print(VN.model_fields.keys())
```

Models ignore unknown fields, so a response carrying extra keys will not raise.
See the [API reference](../reference/entities.md) for each model's fields.
