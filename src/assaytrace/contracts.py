from assaytrace.artifacts import canonical_json


class SourceConflict(ValueError):
    pass


def dedupe_activities(records):
    by_key = {}
    repeated_encounters = 0
    for record in records:
        key = (record["source_id"], record["activity_id"])
        if key in by_key:
            if canonical_json(by_key[key]["source_payload"]) != canonical_json(
                record["source_payload"]
            ):
                raise SourceConflict(f"Conflicting source payload: {key}")
            repeated_encounters += 1
        else:
            by_key[key] = record
    return list(by_key.values()), repeated_encounters
