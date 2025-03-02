SELECT  CAST(id as INT) as user_id, 
        CAST(index as INT) as user_index,
       "Occupation" as occupation,
        TO_TIMESTAMP("Active_Since", 'YY-MM-DD HH24:MI:SS') at time zone 'utc' as active_since
FROM {{ source('recommmender_system_raw', 'users') }}