SELECT  CAST(index as INT),
        CAST(user_id as INT),
        CAST(movie_id as INT),
        CAST(rating as INT),
        TO_TIMESTAMP("Date", 'YY-MM-DD HH24:MI:SS') at time zone 'utc' as date,
        "Unnamed__0" as unnamed__0
FROM {{ source('recommmender_system_raw', 'scores') }}