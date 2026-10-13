"""Чтение писем и источников DLP-инцидентов из представлений PostgreSQL."""


def get_email_body_from_db(conn, search_id, attachment=None):
    """Найти текст письма или имена вложений по уникальному ID теста."""
    if attachment:
        query = """
            SELECT filename
            FROM zinc_v_blob
            WHERE id = (
                SELECT id
                FROM zinc_v_blob
                WHERE text LIKE %s
                ORDER BY id DESC
                LIMIT 1
            )
            AND blob_type = 1
            AND text NOT LIKE %s
        """
        params = (f"%{search_id}%", f"%{search_id}%")

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]

    query = """
        SELECT text
        FROM zinc_v_blob
        WHERE text LIKE %s
        ORDER BY id DESC
        LIMIT 1
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (f"%{search_id}%",))
        result = cursor.fetchone()

    return result[0] if result else None


def get_type_incident_from_db(conn, search_id, expected_source=None):
    """Найти источник DLP-инцидента для письма, при необходимости по типу."""
    query = """
        SELECT source.source
        FROM zinc_v_blob AS blob
        JOIN zinc_v_source AS source ON source.id = blob.id
        WHERE blob.text LIKE %s
          AND (%s IS NULL OR source.source = %s)
        ORDER BY blob.id DESC
        LIMIT 1
    """

    with conn.cursor() as cursor:
        cursor.execute(
            query,
            (
                f"%{search_id}%",
                expected_source,
                expected_source,
            ),
        )
        result = cursor.fetchone()

    return result[0] if result else None
