
CREATE OR REPLACE PROCEDURE GetStoreRevenue (STORE_ID INT)
RETURNS TABLE()
LANGUAGE SQL
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 1,  "minor": 2,  "patch": "6.0" }, "attributes": {  "component": "transact",  "convertedOn": "07-02-2025",  "domain": "test" }}'
EXECUTE AS CALLER
AS

    DECLARE
        ProcedureResultSet RESULTSET;
    BEGIN

        ProcedureResultSet := (
        SELECT
            s.store_id,
            SUM(p.amount) AS total_revenue

        FROM
            payment p

        INNER JOIN
                rental r
                ON p.rental_id = r.rental_id

        INNER JOIN
                staff st
                ON p.staff_id = st.staff_id

        INNER JOIN
                store s
                ON st.store_id = s.store_id

        WHERE
            s.store_id = :STORE_ID
        GROUP BY
            s.store_id);
        RETURN TABLE(ProcedureResultSet);
    END;
;