
CREATE OR REPLACE PROCEDURE TEST_SCHEMA.AddRental (CUSTOMER_ID INT, INVENTORY_ID INT, STAFF_ID INT)
RETURNS TABLE()
LANGUAGE SQL
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 1,  "minor": 2,  "patch": "6.0" }, "attributes": {  "component": "transact",  "convertedOn": "07-02-2025",  "domain": "test" }}'
EXECUTE AS CALLER
AS

    DECLARE
        RENTAL_ID INT;
        RENTAL_DATE TIMESTAMP_NTZ(3) := CURRENT_TIMESTAMP() :: TIMESTAMP;
        ProcedureResultSet RESULTSET;
    BEGIN

         
         

        

        INSERT INTO rental (rental_date, inventory_id, customer_id, staff_id, return_date)

        VALUES (:RENTAL_DATE, :INVENTORY_ID, :CUSTOMER_ID, :STAFF_ID, NULL);
        
        RENTAL_ID :=
        ProcedureResultSet := (



        
        SELECT
            *
        FROM
            rental
        WHERE
            rental_id = :RENTAL_ID);
        RETURN TABLE(ProcedureResultSet);
    END;
;