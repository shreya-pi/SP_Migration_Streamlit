
CREATE OR REPLACE PROCEDURE GetTopRentedMovies ()
RETURNS TABLE()
LANGUAGE SQL
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 1,  "minor": 2,  "patch": "6.0" }, "attributes": {  "component": "transact",  "convertedOn": "07-02-2025",  "domain": "test" }}'
EXECUTE AS CALLER
AS

    DECLARE
        ProcedureResultSet RESULTSET;
    BEGIN

        ProcedureResultSet := (
        SELECT TOP 10
            f.film_id,
            f.title,
            COUNT(r.rental_id) AS total_rentals

        FROM
            rental r

        INNER JOIN
                inventory i
                ON r.inventory_id = i.inventory_id

        INNER JOIN
                film f
                ON i.film_id = f.film_id
        GROUP BY
            f.film_id,
            f.title

        ORDER BY total_rentals DESC);
        RETURN TABLE(ProcedureResultSet);
    END;
;