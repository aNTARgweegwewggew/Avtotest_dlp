def get_email_body_from_db(conn, search_id, attachment=None):

    if attachment:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT filename
                FROM zinc_v_blob
                WHERE id = (
                    SELECT id
                    FROM zinc_v_blob
                    WHERE text LIKE %s
                    LIMIT 1
                )
                AND blob_type = 1
                AND text NOT LIKE %s
                """,
                (f"%{search_id}%", f"%{search_id}%")
            )

            return cursor.fetchall()

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT text
            FROM zinc_v_blob
            WHERE text LIKE %s
            """,
            (f"%{search_id}%",)
        )

        result = cursor.fetchone()

        if result:
            return result[0]

        return None


def get_type_incident_from_db(conn, search_id):

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT source
            FROM zinc_v_source
            WHERE source_type = 17
            AND id = (
                SELECT id
                FROM zinc_v_blob
                WHERE text LIKE %s
                LIMIT 1
            )
            """,
            (f"%{search_id}%",)
        )

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

